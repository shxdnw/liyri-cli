import re
import requests

LRCLIB_BASE = "https://lrclib.net/api"
NETEASE_BASE = "http://music.163.com/api"
USER_AGENT = "liyri-cli/1.0.1 (https://github.com/shxdnw/liyri-cli)"
TIMEOUT = 5

ENABLE_KEYWORD_STRIPPING = True

_LYRICS_CACHE = {}

def _headers():
    return {"User-Agent": USER_AGENT}

def fetch_lyrics(title, artist, album=None, duration_s=None):
    cache_key = (artist.lower(), title.lower())
    if cache_key in _LYRICS_CACHE:
        return _LYRICS_CACHE[cache_key]

    result = _fetch_lyrics_internal(title, artist, album, duration_s)
    
    if result:
        _LYRICS_CACHE[cache_key] = result
        
    return result

def _fetch_lyrics_internal(title, artist, album=None, duration_s=None):
    result = _try_exact_match(title, artist, album, duration_s)
    if result:
        return result

    result = _try_search(title, artist)
    if result:
        return result

    clean_title = re.sub(r"\s*[\(\[].*?[\)\]]", "", title).strip()
    if clean_title != title:
        result = _try_search(clean_title, artist)
        if result:
            return result

    if ENABLE_KEYWORD_STRIPPING:
        keyword_strip = re.sub(r"(?i)[-\s]*(slowed|sped up|nightcore|reverb|superslowed).*$", "", clean_title).strip()
        if keyword_strip and keyword_strip != clean_title:
            result = _try_search(keyword_strip, artist)
            if result:
                return result

    # Fallback to NetEase
    result = _fetch_netease_lyrics(title, artist)
    if result:
        return result

    return None

def _try_exact_match(title, artist, album=None, duration_s=None):
    params = {
        "track_name": title,
        "artist_name": artist,
    }
    if album:
        params["album_name"] = album
    if duration_s and duration_s > 0:
        params["duration"] = int(duration_s)

    try:
        resp = requests.get(
            f"{LRCLIB_BASE}/get",
            params=params,
            headers=_headers(),
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            return _parse_response(data)
    except (requests.RequestException, ValueError):
        pass
    return None

def _try_search(title, artist):
    query = f"{artist} {title}"
    try:
        resp = requests.get(
            f"{LRCLIB_BASE}/search",
            params={"q": query},
            headers=_headers(),
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            results = resp.json()
            if results and isinstance(results, list) and len(results) > 0:
                best = None
                for r in results:
                    if r.get("syncedLyrics"):
                        best = r
                        break
                if best is None:
                    best = results[0]
                return _parse_response(best)
    except (requests.RequestException, ValueError):
        pass
    return None

def _parse_response(data):
    synced_raw = data.get("syncedLyrics", "")
    plain_raw = data.get("plainLyrics", "")

    synced = None
    if synced_raw:
        synced = parse_synced_lyrics(synced_raw)

    plain = None
    if plain_raw:
        plain = [line for line in plain_raw.split("\n")]

    if not synced and not plain:
        return None

    return {
        "synced_lyrics": synced,
        "plain_lyrics": plain,
        "source": "lrclib",
        "track_name": data.get("trackName", ""),
        "artist_name": data.get("artistName", ""),
    }

def _fetch_netease_lyrics(title, artist):
    """Fallback fetcher for NetEase Music."""
    query = f"{artist} {title}"
    headers = {
        "Referer": "http://music.163.com",
        "User-Agent": "Mozilla/5.0"
    }
    
    try:
        # 1. Search for song ID
        resp = requests.get(
            f"{NETEASE_BASE}/search/get",
            params={"s": query, "type": 1, "limit": 5},
            headers=headers,
            timeout=TIMEOUT
        )
        if resp.status_code != 200: return None
        
        results = resp.json().get("result", {}).get("songs", [])
        if not results: return None
        
        # Pick best match (look for title in result)
        song_id = results[0]["id"]
        track_name = results[0].get("name", title)
        artist_name = results[0].get("artists", [{}])[0].get("name", artist)

        # 2. Fetch lyrics by ID
        lyr_resp = requests.get(
            f"{NETEASE_BASE}/song/lyric",
            params={"id": song_id, "lv": 1, "kv": 1, "tv": -1},
            headers=headers,
            timeout=TIMEOUT
        )
        if lyr_resp.status_code != 200: return None
        
        lyr_data = lyr_resp.json()
        lrc_text = lyr_data.get("lrc", {}).get("lyric", "")
        if not lrc_text: return None

        # 3. Parse and return
        synced = parse_synced_lyrics(lrc_text)
        # If synced parsing failed or produced no lines, it might be plain text
        plain = [l.strip() for l in lrc_text.split('\n') if l.strip()] if not synced else [l[1] for l in synced]

        return {
            "synced_lyrics": synced,
            "plain_lyrics": plain,
            "source": "netease",
            "track_name": track_name,
            "artist_name": artist_name
        }
    except Exception:
        return None

def parse_synced_lyrics(lrc_string):
    """
    Robustly parse LRC strings. 
    Handles [mm:ss], [mm:ss.xx], [mm:ss.xxx], [mm:ss.xx-x], 
    and multiple timestamps per line.
    """
    # Regex for [minutes:seconds.fraction] - fraction and suffix are optional
    tag_pattern = re.compile(r"\[(\d+):(\d{2})(?:\.(\d+))?.*?\]")
    lines = []
    
    for raw_line in lrc_string.split("\n"):
        raw_line = raw_line.strip()
        if not raw_line: continue
        
        # Find all timestamps in the line
        matches = list(tag_pattern.finditer(raw_line))
        if not matches: continue
        
        # The text is whatever is left after removing all tags
        text = tag_pattern.sub("", raw_line).strip()
        
        for m in matches:
            try:
                minutes = int(m.group(1))
                seconds = int(m.group(2))
                frac_str = m.group(3)
                
                # Convert fraction (00, 000, 5) to float seconds
                frac = 0.0
                if frac_str:
                    # Handle cases like .5 (500ms), .50 (500ms), .500 (500ms)
                    frac = int(frac_str) / (10 ** len(frac_str))
                
                timestamp = minutes * 60 + seconds + frac
                lines.append((timestamp, text))
            except (ValueError, TypeError):
                continue

    if not lines:
        return None
        
    # LRC lines aren't always in order if there are multiple tags per line
    lines.sort(key=lambda x: x[0])
    return lines
