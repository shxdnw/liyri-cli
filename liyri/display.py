"""Curses-based animated lyrics display."""

import curses
import time
import unicodedata

from liyri import player as mpris


# ──────────────────────────────────────────────
#  Colour & style setup
# ──────────────────────────────────────────────

CP_HEADER    = 1
CP_CURRENT   = 2
CP_NEAR      = 3
CP_FAR       = 4
CP_DIM       = 5
CP_ACCENT    = 6
CP_PROGRESS  = 7
CP_WORD_GLOW = 8
CP_INSTRUMENTAL = 9
CP_BIG_WORD  = 10
CP_PAUSE     = 11

def _init_colors():
    """Set up colour pairs for the UI."""
    curses.start_color()
    curses.use_default_colors()
    try:
        curses.init_pair(CP_HEADER,       curses.COLOR_CYAN,    -1)
        curses.init_pair(CP_CURRENT,      curses.COLOR_WHITE,   -1)
        curses.init_pair(CP_NEAR,         curses.COLOR_CYAN,    -1)
        curses.init_pair(CP_FAR,          curses.COLOR_BLUE,    -1)
        curses.init_pair(CP_DIM,          240,                  -1)
        curses.init_pair(CP_ACCENT,       curses.COLOR_MAGENTA, -1)
        curses.init_pair(CP_PROGRESS,     curses.COLOR_GREEN,   -1)
        curses.init_pair(CP_WORD_GLOW,    curses.COLOR_YELLOW,  -1)
        curses.init_pair(CP_INSTRUMENTAL, curses.COLOR_BLUE,    -1)
        curses.init_pair(CP_BIG_WORD,     curses.COLOR_WHITE,   -1)
        curses.init_pair(CP_PAUSE,        curses.COLOR_YELLOW,  -1)
    except curses.error:
        curses.init_pair(CP_HEADER,       curses.COLOR_CYAN,    -1)
        curses.init_pair(CP_CURRENT,      curses.COLOR_WHITE,   -1)
        curses.init_pair(CP_NEAR,         curses.COLOR_CYAN,    -1)
        curses.init_pair(CP_FAR,          curses.COLOR_BLUE,    -1)
        curses.init_pair(CP_DIM,          curses.COLOR_WHITE,   -1)
        curses.init_pair(CP_ACCENT,       curses.COLOR_MAGENTA, -1)
        curses.init_pair(CP_PROGRESS,     curses.COLOR_GREEN,   -1)
        curses.init_pair(CP_WORD_GLOW,    curses.COLOR_YELLOW,  -1)
        curses.init_pair(CP_INSTRUMENTAL, curses.COLOR_BLUE,    -1)
        curses.init_pair(CP_BIG_WORD,     curses.COLOR_WHITE,   -1)
        curses.init_pair(CP_PAUSE,        curses.COLOR_YELLOW,  -1)


# ──────────────────────────────────────────────
#  Block-letter font (3 rows tall)
# ──────────────────────────────────────────────

_BLOCK_FONT = {
    'A': ["█▀█", "█▀█", "▀ ▀"],
    'B': ["█▀▄", "█▀▄", "▀▀ "],
    'C': ["█▀▀", "█  ", "▀▀▀"],
    'D': ["█▀▄", "█ █", "▀▀ "],
    'E': ["█▀▀", "█▀▀", "▀▀▀"],
    'F': ["█▀▀", "█▀ ", "▀  "],
    'G': ["█▀▀", "█ █", "▀▀▀"],
    'H': ["█ █", "█▀█", "▀ ▀"],
    'I': ["▀█▀", " █ ", "▀█▀"],
    'J': ["  █", "  █", "▀▀ "],
    'K': ["█ █", "█▀▄", "▀ ▀"],
    'L': ["█  ", "█  ", "▀▀▀"],
    'M': ["█▄█", "█ █", "▀ ▀"],
    'N': ["█▀█", "█ █", "▀ ▀"],
    'O': ["█▀█", "█ █", "▀▀▀"],
    'P': ["█▀█", "█▀ ", "▀  "],
    'Q': ["█▀█", "█ █", "▀▀▄"],
    'R': ["█▀█", "█▀▄", "▀ ▀"],
    'S': ["█▀▀", "▀▀█", "▀▀▀"],
    'T': ["▀█▀", " █ ", " ▀ "],
    'U': ["█ █", "█ █", "▀▀▀"],
    'V': ["█ █", "█ █", " ▀ "],
    'W': ["█ █", "█ █", "█▀█"],
    'X': ["█ █", " █ ", "█ █"],
    'Y': ["█ █", " █ ", " ▀ "],
    'Z': ["▀▀█", " █ ", "█▀▀"],
    '0': ["█▀█", "█ █", "▀▀▀"],
    '1': [" █ ", " █ ", " ▀ "],
    '2': ["▀▀█", "█▀▀", "▀▀▀"],
    '3': ["▀▀█", " ▀█", "▀▀▀"],
    '4': ["█ █", "▀▀█", "  ▀"],
    '5': ["█▀▀", "▀▀█", "▀▀▀"],
    '6': ["█▀▀", "█▀█", "▀▀▀"],
    '7': ["▀▀█", "  █", "  ▀"],
    '8': ["█▀█", "█▀█", "▀▀▀"],
    '9': ["█▀█", "▀▀█", "▀▀▀"],
    "'": [" █ ", " ▀ ", "   "],
    ',': ["   ", "   ", " ▄ "],
    '.': ["   ", "   ", " ▀ "],
    '!': [" █ ", " █ ", " ▀ "],
    '?': ["▀▀█", " ▀ ", " ▀ "],
    '-': ["   ", "▀▀▀", "   "],
    ' ': ["   ", "   ", "   "],
    ':': [" ▀ ", "   ", " ▀ "],
    ';': [" ▀ ", "   ", " ▄ "],
    '(': [" █ ", "█  ", " █ "],
    ')': ["█  ", " █ ", "█  "],
    # Cyrillic
    'А': ["█▀█", "█▀█", "▀ ▀"], 'Б': ["█▀▀", "█▀█", "▀▀▀"],
    'В': ["█▀▄", "█▀▄", "▀▀ "], 'Г': ["█▀▀", "█  ", "▀  "],
    'Д': [" █▀", " █ ", "▀▀▀"], 'Е': ["█▀▀", "█▀▀", "▀▀▀"],
    'Ё': ["█▀▀", "█▀▀", "▀▀▀"], 'Ж': ["█▄█", " █ ", "█ █"],
    'З': ["▀▀█", " ▀█", "▀▀▀"], 'И': ["█ █", "█▀█", "█ █"],
    'Й': ["█▄█", "█▀█", "█ █"], 'К': ["█ █", "█▀▄", "▀ ▀"],
    'Л': ["█▀█", "█ █", "▀ ▀"], 'М': ["█▄█", "█ █", "▀ ▀"],
    'Н': ["█ █", "█▀█", "█ █"], 'О': ["█▀█", "█ █", "▀▀▀"],
    'П': ["█▀█", "█ █", "▀ ▀"], 'Р': ["█▀█", "█▀ ", "▀  "],
    'С': ["█▀▀", "█  ", "▀▀▀"], 'Т': ["▀█▀", " █ ", " ▀ "],
    'У': ["█ █", " ▀█", "▀▀ "], 'Ф': ["█▀█", "█╋█", " █ "],
    'Х': ["█ █", " █ ", "█ █"], 'Ц': ["█ █", "█ █", "▀▀▄"],
    'Ч': ["█ █", "▀▀█", "  ▀"], 'Ш': ["█ █", "█ █", "▀▀▀"],
    'Щ': ["█ █", "█ █", "▀▀█"], 'Ъ': ["█  ", "█▀█", "▀▀▀"],
    'Ы': ["█ █", "█▀█", "▀▀▀"], 'Ь': ["█  ", "█▀ ", "▀▀▀"],
    'Э': ["▀▀█", " █▀", "▀▀█"], 'Ю': ["█▀█", "█▀█", "▀ ▀"],
    'Я': ["█▀█", "█▀█", "▀ ▀"],
    # Greek
    'Α': ["█▀█", "█▀█", "▀ ▀"], 'Β': ["█▀▄", "█▀▄", "▀▀ "],
    'Γ': ["█▀▀", "█  ", "▀  "], 'Δ': [" █ ", "█▀█", "▀▀▀"],
    'Ε': ["█▀▀", "█▀▀", "▀▀▀"], 'Ζ': ["▀▀█", " █ ", "█▀▀"],
    'Η': ["█ █", "█▀█", "▀ ▀"], 'Θ': ["█▀█", "█ █", "▀▀▀"],
    'Ι': ["▀█▀", " █ ", "▀█▀"], 'Κ': ["█ █", "█▀▄", "▀ ▀"],
    'Λ': [" █ ", "█ █", "▀ ▀"], 'Μ': ["█▄█", "█ █", "▀ ▀"],
    'Ν': ["█▀█", "█ █", "▀ ▀"], 'Ξ': ["▀▀▀", " █ ", "▀▀▀"],
    'Ο': ["█▀█", "█ █", "▀▀▀"], 'Π': ["█▀█", "█ █", "▀ ▀"],
    'Ρ': ["█▀█", "█▀ ", "▀  "], 'Σ': ["█▀▀", " ▀█", "▀▀▀"],
    'Τ': ["▀█▀", " █ ", " ▀ "], 'Υ': ["█ █", " █ ", " ▀ "],
    'Φ': ["█▀█", "█╋█", " █ "], 'Χ': ["█ █", " █ ", "█ █"],
    'Ψ': ["█ █", "▀█▀", " █ "], 'Ω': ["█▀█", "█ █", "▀ ▀"],
    # Accented Latin & Special
    'Á': [" █ ", "█▀█", "▀ ▀"], 'É': [" █ ", "█▀▀", "▀▀▀"],
    'Í': [" █ ", " █ ", " ▀ "], 'Ó': [" █ ", "█▀█", "▀▀▀"],
    'Ú': [" █ ", "█ █", "▀▀▀"], 'Ñ': ["█▀█", "█ █", "▀ ▀"],
    'Ü': ["█ █", "█ █", "▀▀▀"], 'Ö': ["█ █", "█▀█", "▀▀▀"],
    'Ä': ["█ █", "█▀█", "▀ ▀"], 'Ç': ["█▀▀", "█  ", "▀▀▄"],
    'İ': [" ▄ ", " █ ", " ▀ "],
    # Vietnamese & Special
    'Đ': ["█▀▄", "█╋█", "▀▀ "],
    'ß': ["█▀▄", "█▀▄", "█▀ "],
    'Æ': ["█▀▀", "█▀▀", "▀▀▀"], # Rough approximation
    'Œ': ["█▀█", "█▀█", "▀▀▀"], # Rough approximation
}

_BLOCK_CHAR_W = 3
_BLOCK_GAP = 1


def _char_display_width(ch):
    """Get terminal display width of a character (CJK = 2, others = 1)."""
    cat = unicodedata.east_asian_width(ch)
    return 2 if cat in ('F', 'W') else 1


# ──────────────────────────────────────────────
#  Composition System
# ──────────────────────────────────────────────

_DIACRITIC_TOP = {
    '\u0300': "▀  ", # Grave
    '\u0301': "  ▀", # Acute
    '\u0302': " ▀ ", # Circumflex
    '\u0303': "▀▀▀", # Tilde
    '\u0304': "▀▀▀", # Macron
    '\u0306': "█▄█", # Breve
    '\u0307': " ▀ ", # Dot Above
    '\u0308': "▀ ▀", # Diaeresis/Umlaut
    '\u0309': " ▀█", # Hook Above (Vietnamese)
    '\u030A': " ▀ ", # Ring Above
    '\u030B': "▀ ▀", # Double Acute
    '\u030C': "▀ ▀", # Caron/Hacek
    '\u031B': "  ▀", # Horn (Vietnamese ơ, ư)
}

_DIACRITIC_BOT = {
    '\u0323': " ▄ ", # Dot Below
    '\u0327': "  ▄", # Cedilla
    '\u0328': "  ▄", # Ogonek
}

def _merge_row(row1, row2):
    """Merge two block-pattern rows (logical OR)."""
    res = list(row1)
    for i, c in enumerate(row2):
        if c != ' ' and i < len(res):
            res[i] = c
    return "".join(res)

def _compose_glyph(ch):
    """Try to dynamically build a 4-row glyph for an accented character."""
    ch_upper = ch.upper()
    norm = unicodedata.normalize('NFD', ch_upper)
    base = norm[0]
    diacritics = norm[1:]

    if base not in _BLOCK_FONT:
        return None

    base_glyph = _BLOCK_FONT[base]
    # 4-row system: Row 0 is for accents, Rows 1-3 are the base body.
    rows = ["   ", base_glyph[0], base_glyph[1], base_glyph[2]]
    
    accent_added = False
    for d in diacritics:
        if d in _DIACRITIC_TOP:
            rows[0] = _merge_row(rows[0], _DIACRITIC_TOP[d])
            accent_added = True
        elif d in _DIACRITIC_BOT:
            rows[3] = _merge_row(rows[3], _DIACRITIC_BOT[d])
            accent_added = True

    if not accent_added:
        return None # Fall back to wrapped _BLOCK_FONT search in _get_glyph

    return rows, _BLOCK_CHAR_W


def _get_glyph(ch):
    """Get the 4-row glyph for a character. Falls back to a better block-frame."""
    composed = _compose_glyph(ch)
    if composed:
        return composed
    
    ch_upper = ch.upper()
    if ch_upper in _BLOCK_FONT:
        bg = _BLOCK_FONT[ch_upper]
        # Always wrap in 4 rows for consistency
        return ["   ", bg[0], bg[1], bg[2]], _BLOCK_CHAR_W
    
    # Fallback for complex scripts (Chinese, Arabic, Korean, etc.)
    cw = _char_display_width(ch_upper)
    
    # Clean box-less fallback centering the actual character
    top = "   "
    bot = "   "
    mid_padding = " "
    if cw == 2:
        mid_row = f" {ch_upper}"
        return [top, "   ", mid_row, bot], 3
    else:
        mid_row = f" {ch_upper} "
        return [top, "   ", mid_row, bot], 3


def _render_block_word(word):
    """Render a word as 4-row block text. Handles any Unicode character."""
    word = word.upper()
    rows = ["", "", "", ""]
    for i, ch in enumerate(word):
        glyph, gw = _get_glyph(ch)
        gap = " " * _BLOCK_GAP if i > 0 else ""
        for r in range(4):
            rows[r] += gap + glyph[r]
    return rows


def _block_word_width(word):
    """Calculate char width of a block-rendered word."""
    word = word.upper()
    if not word:
        return 0
    total = 0
    for i, ch in enumerate(word):
        _, gw = _get_glyph(ch)
        if i > 0:
            total += _BLOCK_GAP
        total += gw
    return total


# ──────────────────────────────────────────────
#  Drawing helpers
# ──────────────────────────────────────────────

def _safe_addstr(win, y, x, text, attr=0):
    """Write text to curses window, safely clipping."""
    try:
        h, w = win.getmaxyx()
        if y < 0 or y >= h or x >= w or x < 0:
            return
        max_len = w - x - 1
        if max_len <= 0:
            return
        win.addnstr(y, x, text, max_len, attr)
    except curses.error:
        pass  # silently handle resize/boundary errors


def _center_x(win, text):
    """Return x to centre text horizontally."""
    try:
        _, w = win.getmaxyx()
        return max(0, (w - len(text)) // 2)
    except curses.error:
        return 0


def _format_time(seconds):
    if seconds < 0:
        seconds = 0
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def _draw_progress_bar(win, y, position_s, duration_s, paused=False):
    """Draw a playback progress bar with pause awareness."""
    try:
        h, w = win.getmaxyx()
    except curses.error:
        return
    if y < 0 or y >= h or w < 20:
        return

    bar_width = w - 16
    if bar_width < 5:
        return

    if duration_s <= 0:
        frac = 0
    else:
        frac = max(0.0, min(1.0, position_s / duration_s))
    filled = int(frac * bar_width)

    pos_str = _format_time(position_s)
    dur_str = _format_time(duration_s)

    progress_color = CP_PAUSE if paused else CP_PROGRESS

    _safe_addstr(win, y, 1, pos_str, curses.color_pair(CP_DIM))

    bar_x = len(pos_str) + 2
    _safe_addstr(win, y, bar_x, "─" * bar_width, curses.color_pair(CP_DIM) | curses.A_DIM)
    if filled > 0:
        _safe_addstr(win, y, bar_x, "━" * filled,
                     curses.color_pair(progress_color) | curses.A_BOLD)

    # Playback head
    head_x = bar_x + filled
    if head_x < w - len(dur_str) - 2:
        head_char = "⏸" if paused else "●"
        _safe_addstr(win, y, head_x, head_char,
                     curses.color_pair(progress_color) | curses.A_BOLD)

    _safe_addstr(win, y, w - len(dur_str) - 1, dur_str, curses.color_pair(CP_DIM))


def _draw_box_header(win, title, artist, player_name, paused=False):
    """Draw header box with song info."""
    try:
        h, w = win.getmaxyx()
    except curses.error:
        return 0
    if h < 6 or w < 10:
        return 0

    border = "─" * max(0, w - 2)
    _safe_addstr(win, 0, 0, "╭" + border + "╮", curses.color_pair(CP_HEADER) | curses.A_DIM)

    status_icon = "⏸" if paused else "♫"
    _safe_addstr(win, 1, 0, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)
    _safe_addstr(win, 1, 2, f"{status_icon}  {title}", curses.color_pair(CP_CURRENT) | curses.A_BOLD)
    _safe_addstr(win, 1, w - 1, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)

    _safe_addstr(win, 2, 0, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)
    _safe_addstr(win, 2, 2, f"◈  {artist}", curses.color_pair(CP_ACCENT))
    _safe_addstr(win, 2, w - 1, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)

    _safe_addstr(win, 3, 0, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)
    _safe_addstr(win, 3, 2, f"▶  {player_name}", curses.color_pair(CP_DIM))
    _safe_addstr(win, 3, w - 1, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)

    _safe_addstr(win, 4, 0, "╰" + border + "╯", curses.color_pair(CP_HEADER) | curses.A_DIM)
    return 5


def _get_line_attr(distance):
    if distance == 0:
        return curses.color_pair(CP_CURRENT) | curses.A_BOLD
    elif abs(distance) == 1:
        return curses.color_pair(CP_NEAR)
    elif abs(distance) <= 3:
        return curses.color_pair(CP_FAR)
    else:
        return curses.color_pair(CP_DIM) | curses.A_DIM


def _get_player_state(bus_name):
    """Get position and status from player. Returns (pos_s, duration_s, status) or None."""
    try:
        status = mpris.get_playback_status(bus_name)
        pos_us = mpris.get_position_us(bus_name)
        return pos_us / 1_000_000, status
    except Exception:
        return None


def _check_song_changed(bus_name, current_title):
    """Check if the current song title differs. Returns True if changed."""
    try:
        track = mpris.get_now_playing()
        if track and track["title"] != current_title:
            return True
    except Exception:
        pass
    return False


def _draw_big_word(stdscr, word, cy):
    """Draw a big block-letter word centered at row cy. Returns rows used."""
    try:
        h, w = stdscr.getmaxyx()
    except curses.error:
        return 0

    if not word:
        return 0

    block_rows = _render_block_word(word)
    block_w = _block_word_width(word)

    if block_w > w - 4:
        # Fallback: regular big text
        x = max(0, (w - len(word)) // 2)
        _safe_addstr(stdscr, cy, x, word.upper(),
                     curses.color_pair(CP_BIG_WORD) | curses.A_BOLD)
        return 1
    else:
        x = max(0, (w - block_w) // 2)
        # 4-row system: start 2 rows above the requested center to keep the "body" centered
        start_y = cy - 2
        for r, row in enumerate(block_rows):
            _safe_addstr(stdscr, start_y + r, x, row,
                         curses.color_pair(CP_BIG_WORD) | curses.A_BOLD)
        return 4


def _draw_pause_overlay(stdscr, word, line_text):
    """Draw pause indicator alongside the last word."""
    try:
        h, w = stdscr.getmaxyx()
    except curses.error:
        return

    pause_label = "⏸ paused"
    py = 2 if h > 8 else 0
    _safe_addstr(stdscr, py, w - len(pause_label) - 2, pause_label,
                 curses.color_pair(CP_PAUSE) | curses.A_DIM)


# ──────────────────────────────────────────────
#  FOCUS MODE — big word, one at a time
# ──────────────────────────────────────────────

class PlayerTracker:
    """Manages player state with interpolation for silky smooth sync."""
    def __init__(self, bus_name):
        self.bus_name = bus_name
        self.last_pos = 0.0
        self.last_status = "Stopped"
        self.last_update = time.monotonic()
        self.poll_interval = 0.2
        self.last_poll = 0.0

    def sync(self, force=False):
        """Poll D-Bus and update internal state."""
        now = time.monotonic()
        if force or (now - self.last_poll > self.poll_interval):
            info = mpris.get_player_info(self.bus_name)
            if info:
                new_status, pos_us, _ = info
                actual_pos = pos_us / 1_000_000
                
                if force or new_status != "Playing" or self.last_status != "Playing":
                    self.last_pos = actual_pos
                    self.last_update = now
                else:
                    # Seek detection heuristic
                    expected_pos = self.last_pos + (now - self.last_update)
                    if abs(actual_pos - expected_pos) > 1.0:
                        self.last_pos = actual_pos
                        self.last_update = now
                
                self.last_status = new_status
                self.last_poll = now
            return True
        return False

    def get_pos(self):
        """Get interpolated position."""
        if self.last_status != "Playing":
            return self.last_pos
        return self.last_pos + (time.monotonic() - self.last_update)


def run_focus(stdscr, synced_lyrics, track_info, minimal=False):
    """Display one word at a time with interpolation sync."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(10)  # ~100fps polling for input/timer
    _init_colors()

    bus_name = track_info["bus_name"]
    title = track_info["title"]
    artist = track_info["artist"]
    player_name = track_info["player"]
    duration_s = track_info["duration_us"] / 1_000_000

    tracker = PlayerTracker(bus_name)
    tracker.sync(force=True)

    lines = synced_lyrics
    last_word, last_line_text = "", ""
    last_word_idx, last_line_idx = -1, -1
    last_ui_check = time.monotonic()
    force_redraw = True

    while True:
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key in (ord("q"), ord("Q"), 27): return "quit"
        if key == ord("m"): minimal = not minimal; force_redraw = True
        if key == curses.KEY_RESIZE:
            force_redraw = True
            try: stdscr.clear()
            except curses.error: pass

        tracker.sync()
        if tracker.last_status == "Stopped": return "stopped"
        
        pos_s = tracker.get_pos()
        paused = (tracker.last_status == "Paused")
        now = time.monotonic()

        # Song change check (every 1s)
        if now - last_ui_check > 1.0:
            last_ui_check = now
            if _check_song_changed(bus_name, title): return "song_changed"

        # Find current line/word from interpolated position
        current_line_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if pos_s >= lines[i][0]:
                current_line_idx = i
                break

        current_word, current_word_idx, full_line_text = "", -1, ""
        if current_line_idx >= 0:
            full_line_text = lines[current_line_idx][1]
            words = full_line_text.split() if full_line_text.strip() else []
            if words:
                ld = lines[current_line_idx+1][0] - lines[current_line_idx][0] if current_line_idx < len(lines)-1 else 5.0
                
                # Detect instrumental gap: if next line is far away, don't stretch words.
                # Words should take at most ~0.8s each, or 5s total for the line.
                active_duration = min(ld, max(5.0, len(words) * 0.8))
                el = pos_s - lines[current_line_idx][0]
                
                if el > active_duration and ld > active_duration + 2.0:
                    # Instrumental gap reached
                    current_word, current_word_idx = "♫", -1
                else:
                    wi = int((el / active_duration) * len(words)) if active_duration > 0 else 0
                    wi = max(0, min(wi, len(words)-1))
                    current_word, current_word_idx = words[wi], wi
            else:
                current_word = "♫"
                full_line_text = " "
        else:
            current_word = "♫"
            full_line_text = " "

        display_word = current_word or last_word
        if current_word == "♫":
            display_line = full_line_text # Keep showing it but it will be dimmed
        else:
            display_line = full_line_text if full_line_text.strip() else last_line_text

        if current_word:
            last_word, last_line_text, last_word_idx = current_word, full_line_text, current_word_idx

        # Draw decision
        if force_redraw or current_word_idx != last_word_idx or current_line_idx != last_line_idx or (now % 0.1 < 0.02):
            force_redraw = False
            try:
                stdscr.erase()
                h, w = stdscr.getmaxyx()
                if h < 5 or w < 10: continue

                if minimal:
                    if display_word: _draw_big_word(stdscr, display_word, h // 2)
                    if paused: _draw_pause_overlay(stdscr, display_word, display_line)
                else:
                    icon = "⏸" if paused else "♫"
                    info = f"{icon} {title}  ─  {artist}  [{player_name}]"
                    _safe_addstr(stdscr, 0, _center_x(stdscr, info), info, curses.color_pair(CP_HEADER))
                    _safe_addstr(stdscr, 1, 1, "─"*(w-2), curses.color_pair(CP_DIM)|curses.A_DIM)
                    
                    if display_word:
                        _draw_big_word(stdscr, display_word, h//2 - 1)
                        if display_line.strip():
                            cy = h//2 + 2
                            cx = _center_x(stdscr, display_line)
                            _safe_addstr(stdscr, cy, cx, display_line, curses.color_pair(CP_DIM))
                            words = display_line.split()
                            wi = current_word_idx if current_word_idx >= 0 else last_word_idx
                            if 0 <= wi < len(words):
                                before = " ".join(words[:wi])
                                hx = cx + len(before) + (1 if before else 0)
                                _safe_addstr(stdscr, cy, hx, words[wi], curses.color_pair(CP_CURRENT)|curses.A_BOLD)
                    
                    if h > 6: _draw_progress_bar(stdscr, h-2, pos_s, duration_s, paused)
                    if h > 4: _safe_addstr(stdscr, h-1, _center_x(stdscr, "q quit  m minimal"), "q quit  m minimal", curses.color_pair(CP_DIM)|curses.A_DIM)
                
                stdscr.refresh()
            except curses.error: pass

        last_line_idx, last_word_idx = current_line_idx, current_word_idx
        time.sleep(0.016)  # ~60fps target loop speed


def run_focus_plain(stdscr, plain_lines, track_info, speed=1.0, minimal=False):
    """Focus mode for plain lyrics with timer-based interpolation."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(10)
    _init_colors()

    bus_name = track_info["bus_name"]
    title, artist = track_info["title"], track_info["artist"]
    player_name = track_info["player"]
    duration_s = track_info["duration_us"] / 1_000_000

    word_list = []
    for line in plain_lines:
        words = line.split() if line.strip() else []
        if not words: word_list.append(("", "", -1))
        else:
            for wi, w in enumerate(words): word_list.append((w, line, wi))

    if not word_list: return "quit"
    word_delay = max(0.08, min(2.0/speed, (duration_s * 0.8) / len(word_list))) if duration_s > 0 else 0.25/speed

    tracker = PlayerTracker(bus_name)
    tracker.sync(force=True)

    current_wi = 0
    last_advance = time.monotonic()
    last_ui_check = time.monotonic()
    force_redraw = True

    while current_wi < len(word_list):
        try:
            key = stdscr.getch()
        except curses.error: key = -1
        if key in (ord("q"), ord("Q"), 27): return "quit"
        if key == ord("m"): minimal = not minimal; force_redraw = True
        if key == curses.KEY_RESIZE: force_redraw = True; stdscr.clear()

        tracker.sync()
        if tracker.last_status == "Stopped": return "stopped"
        
        pos_s, paused = tracker.get_pos(), tracker.last_status == "Paused"
        now = time.monotonic()

        if now - last_ui_check > 1.0:
            last_ui_check = now
            if _check_song_changed(bus_name, title): return "song_changed"

        if not paused:
            delay = word_delay if word_list[current_wi][0] else word_delay * 3
            if now - last_advance > delay:
                current_wi += 1
                last_advance = now
                force_redraw = True

        if current_wi >= len(word_list): break
        cw, fl, wil = word_list[current_wi]

        if force_redraw or (now % 0.1 < 0.02):
            force_redraw = False
            try:
                stdscr.erase()
                h, w = stdscr.getmaxyx()
                if h < 5 or w < 10: continue

                if minimal:
                    if cw: _draw_big_word(stdscr, cw, h//2)
                    if paused: _draw_pause_overlay(stdscr, cw, fl)
                else:
                    icon = "⏸" if paused else "♫"
                    info = f"{icon} {title}  ─  {artist} [{player_name}]"
                    _safe_addstr(stdscr, 0, _center_x(stdscr, info), info, curses.color_pair(CP_HEADER))
                    _safe_addstr(stdscr, 1, 1, "─"*(w-2), curses.color_pair(CP_DIM)|curses.A_DIM)
                    if cw:
                        _draw_big_word(stdscr, cw, h//2 - 1)
                        if fl.strip():
                            cy, cx = h//2 + 2, _center_x(stdscr, fl)
                            _safe_addstr(stdscr, cy, cx, fl, curses.color_pair(CP_DIM))
                            words = fl.split()
                            if 0 <= wil < len(words):
                                before = " ".join(words[:wil])
                                hx = cx + len(before) + (1 if before else 0)
                                _safe_addstr(stdscr, cy, hx, words[wil], curses.color_pair(CP_CURRENT)|curses.A_BOLD)
                    if h > 6: _draw_progress_bar(stdscr, h-2, pos_s, duration_s, paused)
                    if h > 4: _safe_addstr(stdscr, h-1, _center_x(stdscr, "q quit  m minimal"), "q quit  m minimal", curses.color_pair(CP_DIM)|curses.A_DIM)
                stdscr.refresh()
            except curses.error: pass
        time.sleep(0.016)

    return "finished"


# ──────────────────────────────────────────────
#  SCROLL MODE — synced lyrics scroll view
# ──────────────────────────────────────────────

def run_synced(stdscr, synced_lyrics, track_info):
    """Display synced lyrics scrolling with silky interpolation."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(10)
    _init_colors()

    bus_name = track_info["bus_name"]
    title, artist = track_info["title"], track_info["artist"]
    player_name = track_info["player"]
    duration_s = track_info["duration_us"] / 1_000_000

    tracker = PlayerTracker(bus_name)
    tracker.sync(force=True)

    lines = synced_lyrics
    current_scroll = 0.0
    last_ui_check = time.monotonic()

    while True:
        try:
            key = stdscr.getch()
        except curses.error: key = -1
        if key in (ord("q"), ord("Q"), 27): return "quit"
        if key == curses.KEY_RESIZE: stdscr.clear()

        tracker.sync()
        if tracker.last_status == "Stopped": return "stopped"
        
        pos_s, paused = tracker.get_pos(), tracker.last_status == "Paused"
        now = time.monotonic()

        if now - last_ui_check > 1.0:
            last_ui_check = now
            if _check_song_changed(bus_name, title): return "song_changed"

        # Find current line
        current_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if pos_s >= lines[i][0]:
                current_idx = i
                break

        # Word reveal
        word_reveal = 0
        words = []
        if current_idx >= 0:
            text = lines[current_idx][1]
            words = text.split() if text else []
            ld = lines[current_idx+1][0] - lines[current_idx][0] if current_idx < len(lines)-1 else 5.0
            el = pos_s - lines[current_idx][0]
            if words and ld > 0: word_reveal = min(len(words), int((el / ld) * len(words)) + 1)
            else: word_reveal = len(words)

        # Smooth scroll
        target = float(current_idx) if current_idx >= 0 else 0.0
        current_scroll += (target - current_scroll) * 0.18

        # Draw
        try:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            if h < 6 or w < 10: continue

            header_h = _draw_box_header(stdscr, title, artist, player_name, paused)
            top, bottom = header_h + 1, h - 3
            height = bottom - top
            if height < 3:
                stdscr.refresh()
                continue

            center_y = top + height // 2
            for i, (ts, text) in enumerate(lines):
                dist = i - current_idx
                vis_off = i - current_scroll
                dy = center_y + int(vis_off)
                if dy < top or dy >= bottom: continue

                if not text.strip():
                    if dist == 0:
                        m = "· · ·"
                        _safe_addstr(stdscr, dy, _center_x(stdscr, m), m, curses.color_pair(CP_INSTRUMENTAL)|curses.A_DIM)
                    continue

                if dist == 0 and words:
                    vis, hid = " ".join(words[:word_reveal]), " ".join(words[word_reveal:])
                    x = _center_x(stdscr, text)
                    _safe_addstr(stdscr, dy, x, vis, curses.color_pair(CP_CURRENT)|curses.A_BOLD)
                    if hid: _safe_addstr(stdscr, dy, x + len(vis) + 1, hid, curses.color_pair(CP_DIM)|curses.A_DIM)
                else:
                    _safe_addstr(stdscr, dy, _center_x(stdscr, text), text, _get_line_attr(dist))

            if h > 5: _draw_progress_bar(stdscr, h - 2, pos_s, duration_s, paused)
            _safe_addstr(stdscr, h - 1, _center_x(stdscr, "q quit  ─  liyri"), "q quit  ─  liyri", curses.color_pair(CP_DIM)|curses.A_DIM)
            stdscr.refresh()
        except curses.error: pass
        time.sleep(0.016)


def run_static(stdscr, plain_lines, track_info, speed=1.0):
    """Display plain lyrics with interpolated animation."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(10)
    _init_colors()

    bus_name = track_info["bus_name"]
    title, artist = track_info["title"], track_info["artist"]
    player_name = track_info["player"]
    duration_s = track_info["duration_us"] / 1_000_000

    lines = [l for l in plain_lines if l.strip()] # filter early for easier index
    tracker = PlayerTracker(bus_name)
    tracker.sync(force=True)

    word_delay = max(0.08, min(2.0/speed, (duration_s * 0.8) / sum(len(l.split()) for l in lines))) if duration_s > 0 and lines else 0.08/speed
    current_line, word_idx = 0, 0
    last_word_time = time.monotonic()
    current_scroll = 0.0
    last_ui_check = time.monotonic()
    completed = set()

    while True:
        try:
            key = stdscr.getch()
        except curses.error: key = -1
        if key in (ord("q"), ord("Q"), 27): return "quit"
        if key == curses.KEY_RESIZE: stdscr.clear()

        tracker.sync()
        if tracker.last_status == "Stopped": return "stopped"
        
        pos_s, paused = tracker.get_pos(), tracker.last_status == "Paused"
        now = time.monotonic()

        if now - last_ui_check > 1.0:
            last_ui_check = now
            if _check_song_changed(bus_name, title): return "song_changed"

        if not paused and current_line < len(lines):
            lt = lines[current_line]
            lw = lt.split()
            if not lw or word_idx >= len(lw):
                if now - last_word_time > (0.4/speed if not lw else 0.5/speed):
                    completed.add(current_line)
                    current_line += 1
                    word_idx, last_word_time = 0, now
            elif now - last_word_time > word_delay:
                word_idx += 1
                last_word_time = now
        elif current_line >= len(lines): return "finished"

        current_scroll += (float(current_line) - current_scroll) * 0.15

        try:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            if h < 6 or w < 10: continue

            header_h = _draw_box_header(stdscr, title, artist, player_name, paused)
            top, bottom = header_h + 1, h - 3
            height = bottom - top
            if height < 3:
                stdscr.refresh()
                continue

            center_y = top + height // 2
            for i, text in enumerate(lines):
                dist = i - current_line
                vis_off = i - current_scroll
                dy = center_y + int(vis_off)
                if dy < top or dy >= bottom: continue

                if i == current_line:
                    lw = text.split()
                    vis, hid = " ".join(lw[:word_idx]), " ".join(lw[word_idx:])
                    x = _center_x(stdscr, text)
                    _safe_addstr(stdscr, dy, x, vis, curses.color_pair(CP_CURRENT)|curses.A_BOLD)
                    if hid: _safe_addstr(stdscr, dy, x + len(vis) + (1 if vis else 0), hid, curses.color_pair(CP_DIM)|curses.A_DIM)
                elif i in completed:
                    _safe_addstr(stdscr, dy, _center_x(stdscr, text), text, _get_line_attr(dist))
                elif abs(dist) <= 4:
                    _safe_addstr(stdscr, dy, _center_x(stdscr, text), text, curses.color_pair(CP_DIM)|curses.A_DIM)

            if h > 5: _draw_progress_bar(stdscr, h - 2, pos_s, duration_s, paused)
            _safe_addstr(stdscr, h - 1, _center_x(stdscr, "q quit  ─  liyri"), "q quit  ─  liyri", curses.color_pair(CP_DIM)|curses.A_DIM)
            stdscr.refresh()
        except curses.error: pass
        time.sleep(0.016)


# ──────────────────────────────────────────────
#  Waiting / utility screens
# ──────────────────────────────────────────────

def run_waiting(stdscr, player_name_filter=None):
    """Wait for media to start playing. Returns track_info or None."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)
    _init_colors()

    dots = 0
    last_dot = time.monotonic()

    while True:
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1
        if key in (ord("q"), ord("Q"), 27):
            return None
        if key == curses.KEY_RESIZE:
            try:
                stdscr.clear()
            except curses.error:
                pass

        now = time.monotonic()
        if now - last_dot > 0.5:
            dots = (dots + 1) % 4
            last_dot = now

        track = mpris.get_now_playing(player_name_filter)
        if track:
            return track

        try:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
        except curses.error:
            time.sleep(0.100)
            continue

        icon = "♫"
        dot_str = "." * dots + " " * (3 - dots)
        msg = f"  waiting for media{dot_str}"
        cy = h // 2
        _safe_addstr(stdscr, cy - 1, _center_x(stdscr, icon), icon,
                     curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        _safe_addstr(stdscr, cy + 1, _center_x(stdscr, msg), msg,
                     curses.color_pair(CP_DIM))

        hint = "q quit  ─  play something to begin"
        _safe_addstr(stdscr, h - 1, _center_x(stdscr, hint), hint,
                     curses.color_pair(CP_DIM) | curses.A_DIM)

        try:
            stdscr.refresh()
        except curses.error:
            pass
        time.sleep(0.050)


def show_fetching(stdscr, title, artist):
    """Brief fetching indicator."""
    try:
        _init_colors()
        curses.curs_set(0)
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        icon = "♫"
        _safe_addstr(stdscr, h // 2, _center_x(stdscr, icon), icon,
                     curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        stdscr.refresh()
    except curses.error:
        pass
