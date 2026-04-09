"""Lyrics fetching from LRCLIB API."""

import re
import requests

LRCLIB_BASE = "https://lrclib.net/api"
USER_AGENT = "liyri-cli/1.0.0 (https://github.com/shxdnw/liyri-cli)"
TIMEOUT = 5

ENABLE_KEYWORD_STRIPPING = True

# Simple in-memory cache to avoid redundant API calls
_LYRICS_CACHE = {}


def _headers():
    return {"User-Agent": USER_AGENT}


def fetch_lyrics(title, artist, album=None, duration_s=None):
    """
    Fetch lyrics for a track from LRCLIB with caching.
    """
    cache_key = (artist.lower(), title.lower())
    if cache_key in _LYRICS_CACHE:
        return _LYRICS_CACHE[cache_key]

    result = _fetch_lyrics_internal(title, artist, album, duration_s)
    
    if result:
        _LYRICS_CACHE[cache_key] = result
        
    return result


def _fetch_lyrics_internal(title, artist, album=None, duration_s=None):
    """Internal logic to fetch lyrics from LRCLIB."""
    result = _try_exact_match(title, artist, album, duration_s)
    if result:
        return result

    result = _try_search(title, artist)
    if result:
        return result

    # Try with simplified title (remove parenthetical info)
    clean_title = re.sub(r"\s*[\(\[].*?[\)\]]", "", title).strip()
    if clean_title != title:
        result = _try_search(clean_title, artist)
        if result:
            return result

    # Try stripping common modifiers like "slowed", "sped up", "nightcore", etc.
    # We do a case-insensitive regex removing a trailing dash or words.
    if ENABLE_KEYWORD_STRIPPING:
        keyword_strip = re.sub(r"(?i)[-\s]*(slowed|sped up|nightcore|reverb|superslowed).*$", "", clean_title).strip()
        if keyword_strip and keyword_strip != clean_title:
            result = _try_search(keyword_strip, artist)
            if result:
                return result

    return None


def _try_exact_match(title, artist, album=None, duration_s=None):
    """Try LRCLIB exact GET endpoint."""
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
    """Try LRCLIB search endpoint."""
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
                # Pick the best match — prefer one with synced lyrics
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
    """Parse a single LRCLIB response object into our format."""
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


def parse_synced_lyrics(lrc_string):
    """
    Parse LRC-format synced lyrics.

    Input:  '[01:23.45] Some lyric line'
    Output: [(83.45, 'Some lyric line'), ...]
    """
    pattern = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2,3})\]\s*(.*)")
    lines = []
    for raw_line in lrc_string.split("\n"):
        raw_line = raw_line.strip()
        m = pattern.match(raw_line)
        if m:
            minutes = int(m.group(1))
            seconds = int(m.group(2))
            centis = m.group(3)
            if len(centis) == 2:
                frac = int(centis) / 100.0
            else:
                frac = int(centis) / 1000.0
            timestamp = minutes * 60 + seconds + frac
            text = m.group(4)
            lines.append((timestamp, text))
    return lines if lines else None
