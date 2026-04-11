import re
import requests
from thefuzz import fuzz

LRCLIB_BASE = "https://lrclib.net"
NETEASE_BASE = "http://music.163.com/api"
USER_AGENT = "liyri-cli/1.2.0"
TIMEOUT = 5

_LYRICS_CACHE = {}

def fetch_lyrics(title, artist, album=None, duration_s=None):
    cache_key = (artist.lower(), title.lower())
    if cache_key in _LYRICS_CACHE:
        return _LYRICS_CACHE[cache_key]

    result = _fetch_lyrics_internal(title, artist, album, duration_s)
    if result:
        _LYRICS_CACHE[cache_key] = result
    return result

def _fetch_lyrics_internal(title, artist, album=None, duration_s=None):
    res = _try_exact_match(title, artist, album, duration_s)
    if res: return res

    res = _try_search(title, artist)
    if res: return res

    clean_title = re.sub(r"\s*[\(\[].*?[\)\]]", "", title).strip()
    if clean_title != title:
        res = _try_search(clean_title, artist)
        if res: return res

    res = _fetch_netease_lyrics(title, artist)
    return res

def _try_exact_match(title, artist, album=None, duration_s=None):
    params = {"track_name": title, "artist_name": artist}
    if album: params["album_name"] = album
    if duration_s: params["duration"] = int(duration_s)

    try:
        resp = requests.get(f"{LRCLIB_BASE}/api/get", params=params, timeout=TIMEOUT)
        if resp.status_code == 200:
            return _parse_response(resp.json())
    except: pass
    return None

def _calculate_match_score(target_title, target_artist, result_title, result_artist):
    target = f"{target_artist} {target_title}".lower()
    result = f"{result_artist} {result_title}".lower()
    return fuzz.token_set_ratio(target, result)

def _try_search(title, artist):
    try:
        resp = requests.get(f"{LRCLIB_BASE}/api/search", params={"q": f"{artist} {title}"}, timeout=TIMEOUT)
        if resp.status_code == 200:
            results = resp.json()
            if results and isinstance(results, list):
                for r in results:
                    r_title, r_artist = r.get("trackName", "").lower(), r.get("artistName", "").lower()
                    if r_title == title.lower() and r_artist == artist.lower() and r.get("syncedLyrics"):
                        return _parse_response(r)

                scored = []
                for r in results:
                    score = _calculate_match_score(title, artist, r.get("trackName", ""), r.get("artistName", ""))
                    if r.get("syncedLyrics"): score += 5
                    scored.append((score, r))
                
                scored.sort(key=lambda x: x[0], reverse=True)
                if scored and scored[0][0] >= 80:
                    return _parse_response(scored[0][1])
    except: pass
    return None

def _parse_response(data):
    synced_raw = data.get("syncedLyrics", "")
    plain_raw = data.get("plainLyrics", "")
    synced, has_k = parse_synced_lyrics(synced_raw) if synced_raw else (None, False)
    plain = [l for l in plain_raw.split("\n")] if plain_raw else None
    if not synced and not plain: return None
    return {
        "synced_lyrics": synced, "plain_lyrics": plain, "source": "lrclib",
        "has_karaoke": has_k,
        "track_name": data.get("trackName", ""), "artist_name": data.get("artistName", "")
    }

def _parse_timestamp(m):
    try:
        min, sec = int(m.group(1)), int(m.group(2))
        frac = int(m.group(3)) / (10 ** len(m.group(3))) if m.group(3) else 0.0
        return min * 60 + sec + frac
    except: return 0.0

def _fetch_netease_lyrics(title, artist):
    try:
        h = {"Referer": "http://music.163.com", "User-Agent": "Mozilla/5.0"}
        resp = requests.get(f"{NETEASE_BASE}/search/get", params={"s": f"{artist} {title}", "type": 1, "limit": 5}, headers=h, timeout=TIMEOUT)
        if resp.status_code != 200: return None
        
        songs = resp.json().get("result", {}).get("songs", [])
        if not songs: return None
        
        scored = []
        for s in songs:
            score = _calculate_match_score(title, artist, s.get("name", ""), s.get("artists", [{}])[0].get("name", ""))
            scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored or scored[0][0] < 70: return None
        
        sid = scored[0][1]["id"]
        lyr_resp = requests.get(f"{NETEASE_BASE}/song/lyric", params={"id": sid, "lv": 1, "kv": 1, "tv": -1}, headers=h, timeout=TIMEOUT)
        if lyr_resp.status_code != 200: return None
        
        data = lyr_resp.json()
        lrc, krc = data.get("lrc", {}).get("lyric", ""), data.get("klyric", {}).get("lyric", "")
        best = krc if krc else lrc
        if not best: return None

        synced, has_k = parse_synced_lyrics(best)
        plain = [l.strip() for l in best.split('\n') if l.strip()] if not synced else [l["text"] for l in synced]
        return {
            "synced_lyrics": synced, "plain_lyrics": plain, "source": "netease",
            "has_karaoke": has_k,
            "track_name": scored[0][1].get("name", title), "artist_name": scored[0][1].get("artists", [{}])[0].get("name", artist)
        }
    except: return None

def parse_synced_lyrics(lrc_string):
    ltag = re.compile(r"\[(\d+):(\d{2})(?:\.(\d+))?.*?\]")
    wtag = re.compile(r"<(\d+):(\d{2})(?:\.(\d+))?.*?>")
    lines = []
    
    for raw in lrc_string.split("\n"):
        raw = raw.strip()
        if not raw: continue
        matches = list(ltag.finditer(raw))
        if not matches: continue
        
        content = ltag.sub("", raw).strip()
        if not content: continue
        
        syllables = []
        wmatches = list(wtag.finditer(content))
        if wmatches:
            for i, m in enumerate(wmatches):
                t = _parse_timestamp(m)
                end = wmatches[i+1].start() if i+1 < len(wmatches) else len(content)
                text = content[m.end():end].strip()
                if text: syllables.append({"time": t, "text": text})
            content = wtag.sub("", content).strip()
        
        for m in matches:
            lines.append({"time": _parse_timestamp(m), "text": content, "syllables": syllables})

    if not lines: return None
    lines.sort(key=lambda x: x["time"])
    
    # Check if we have real karaoke data before guessing
    has_karaoke = any(l["syllables"] for l in lines)

    for i in range(len(lines)):
        l = lines[i]
        if not l["syllables"] and l["text"].strip():
            dur = max(0.5, lines[i+1]["time"] - l["time"]) if i+1 < len(lines) else 5.0
            words = l["text"].split()
            if words:
                wdur = dur / len(words)
                for j, w in enumerate(words):
                    l["syllables"].append({"time": l["time"] + (j * wdur), "text": w})
    return lines, has_karaoke
