"""Curses-based animated lyrics display."""

import curses
import time
import unicodedata
import random

from liyri import player as mpris


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
    'Á': [" █ ", "█▀█", "▀ ▀"], 'É': [" █ ", "█▀▀", "▀▀▀"],
    'Í': [" █ ", " █ ", " ▀ "], 'Ó': [" █ ", "█▀█", "▀▀▀"],
    'Ú': [" █ ", "█ █", "▀▀▀"], 'Ñ': ["█▀█", "█ █", "▀ ▀"],
    'Ü': ["█ █", "█ █", "▀▀▀"], 'Ö': ["█ █", "█▀█", "▀▀▀"],
    'Ä': ["█ █", "█▀█", "▀ ▀"], 'Ç': ["█▀▀", "█  ", "▀▀▄"],
    'İ': [" ▄ ", " █ ", " ▀ "],
    'Đ': ["█▀▄", "█╋█", "▀▀ "],
    'ß': ["█▀▄", "█▀▄", "█▀ "],
    'Æ': ["█▀▀", "█▀▀", "▀▀▀"],
    'Œ': ["█▀█", "█▀█", "▀▀▀"],
}

_BLOCK_CHAR_W = 3
_BLOCK_GAP = 1

def _char_display_width(ch):
    cat = unicodedata.east_asian_width(ch)
    return 2 if cat in ('F', 'W') else 1

_DIACRITIC_TOP = {
    '\u0300': "▀  ", '\u0301': "  ▀", '\u0302': " ▀ ", '\u0303': "▀▀▀",
    '\u0304': "▀▀▀", '\u0306': "█▄█", '\u0307': " ▀ ", '\u0308': "▀ ▀",
    '\u0309': " ▀█", '\u030A': " ▀ ", '\u030B': "▀ ▀", '\u030C': "▀ ▀",
    '\u031B': "  ▀",
}
_DIACRITIC_BOT = {'\u0323': " ▄ ", '\u0327': "  ▄", '\u0328': "  ▄"}

def _merge_row(row1, row2):
    res = list(row1)
    for i, c in enumerate(row2):
        if c != ' ' and i < len(res): res[i] = c
    return "".join(res)

def _compose_glyph(ch):
    ch_upper = ch.upper()
    norm = unicodedata.normalize('NFD', ch_upper)
    base, diacritics = norm[0], norm[1:]
    if base not in _BLOCK_FONT: return None
    bg = _BLOCK_FONT[base]
    rows = ["   ", bg[0], bg[1], bg[2]]
    accent = False
    for d in diacritics:
        if d in _DIACRITIC_TOP: rows[0] = _merge_row(rows[0], _DIACRITIC_TOP[d]); accent=True
        elif d in _DIACRITIC_BOT: rows[3] = _merge_row(rows[3], _DIACRITIC_BOT[d]); accent=True
    return (rows, _BLOCK_CHAR_W) if accent else None

def _get_glyph(ch):
    comp = _compose_glyph(ch)
    if comp: return comp
    cu = ch.upper()
    if cu in _BLOCK_FONT: return (["   ", _BLOCK_FONT[cu][0], _BLOCK_FONT[cu][1], _BLOCK_FONT[cu][2]], _BLOCK_CHAR_W)
    cw = _char_display_width(cu)
    row = f" {cu}" if cw == 2 else f" {cu} "
    return (["   ", "   ", row, "   "], 3)

def _render_block_word(word):
    word = word.upper()
    rows = ["", "", "", ""]
    for i, ch in enumerate(word):
        glyph, gw = _get_glyph(ch)
        gap = " " * _BLOCK_GAP if i > 0 else ""
        for r in range(4): rows[r] += gap + glyph[r]
    return rows

def _block_word_width(word):
    if not word: return 0
    total = 0
    for i, ch in enumerate(word.upper()):
        _, gw = _get_glyph(ch)
        if i > 0: total += _BLOCK_GAP
        total += gw
    return total

class Particle:
    def __init__(self, h, w):
        self.y = random.uniform(0, h)
        self.x = random.uniform(0, w)
        self.char = random.choice(["·", "·", "·", "+", "*"])
        self.speed = random.uniform(0.05, 0.25)

class ParticleEngine:
    def __init__(self, h, w, count=30):
        self.h, self.w = h, w
        self.particles = [Particle(h, w) for _ in range(count)]
        self.enabled = True
    def update(self, h, w):
        self.h, self.w = h, w
        for p in self.particles:
            p.y += p.speed
            if p.y >= h: p.y = 0; p.x = random.uniform(0, w)
    def draw(self, stdscr, intensity="low"):
        if not self.enabled: return
        attr = curses.color_pair(CP_DIM)
        if intensity == "low": attr |= curses.A_DIM
        for p in self.particles: _safe_addstr(stdscr, int(p.y), int(p.x), p.char, attr)

def _safe_addstr(win, y, x, text, attr=0):
    try:
        h, w = win.getmaxyx()
        if y < 0 or y >= h or x >= w or x < 0: return
        win.addnstr(y, x, text, w - x - 1, attr)
    except: pass

def _center_x(win, text):
    try: return max(0, (win.getmaxyx()[1] - len(text)) // 2)
    except: return 0

def _format_time(s):
    if s < 0: s = 0
    return f"{int(s)//60:02d}:{int(s)%60:02d}"

def _draw_progress_bar(win, y, pos, dur, paused=False):
    try: h, w = win.getmaxyx()
    except: return
    if y < 0 or y >= h or w < 20: return
    bw = w - 16
    if bw < 5: return
    frac = max(0.0, min(1.0, pos / dur)) if dur > 0 else 0
    filled = int(frac * bw)
    col = CP_PAUSE if paused else CP_PROGRESS
    _safe_addstr(win, y, 1, _format_time(pos), curses.color_pair(CP_DIM))
    bx = len(_format_time(pos)) + 2
    _safe_addstr(win, y, bx, "─" * bw, curses.color_pair(CP_DIM) | curses.A_DIM)
    if filled > 0: _safe_addstr(win, y, bx, "━" * filled, curses.color_pair(col) | curses.A_BOLD)
    hx = bx + filled
    if hx < w - 7: _safe_addstr(win, y, hx, "⏸" if paused else "●", curses.color_pair(col) | curses.A_BOLD)
    _safe_addstr(win, y, w - 6, _format_time(dur), curses.color_pair(CP_DIM))

def _draw_box_header(win, title, artist, player, paused=False, precision=False):
    try: h, w = win.getmaxyx()
    except: return 0
    if h < 6 or w < 10: return 0
    b = "─" * max(0, w - 2)
    _safe_addstr(win, 0, 0, "╭" + b + "╮", curses.color_pair(CP_HEADER) | curses.A_DIM)
    _safe_addstr(win, 1, 0, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)
    _safe_addstr(win, 1, 2, f"{'⏸' if paused else '♫'}  {title}", curses.color_pair(CP_CURRENT) | curses.A_BOLD)
    _safe_addstr(win, 1, w - 1, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)
    _safe_addstr(win, 2, 0, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)
    _safe_addstr(win, 2, 2, f"◈  {artist}", curses.color_pair(CP_ACCENT))
    _safe_addstr(win, 2, w - 1, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)
    _safe_addstr(win, 3, 0, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)
    tag = "*" if precision else ""
    _safe_addstr(win, 3, 2, f"▶  [{player}]{tag}", curses.color_pair(CP_DIM))
    _safe_addstr(win, 3, w - 1, "│", curses.color_pair(CP_HEADER) | curses.A_DIM)
    _safe_addstr(win, 4, 0, "╰" + b + "╯", curses.color_pair(CP_HEADER) | curses.A_DIM)
    return 5

def _draw_big_word(stdscr, word, cy, attr=None):
    if attr is None: attr = curses.color_pair(CP_BIG_WORD) | curses.A_BOLD
    try: h, w = stdscr.getmaxyx()
    except: return 0
    if not word: return 0
    br = _render_block_word(word)
    bw = _block_word_width(word)
    if bw > w - 4:
        x = max(0, (w - len(word)) // 2)
        _safe_addstr(stdscr, cy, x, word.upper(), attr)
        return 1
    else:
        x, sy = max(0, (w - bw) // 2), cy - 2
        for r, row in enumerate(br): _safe_addstr(stdscr, sy + r, x, row, attr)
        return 4

def _draw_pause_overlay(s, w, l):
    try: h, w_t = s.getmaxyx()
    except: return
    p = "⏸ paused"
    py = 2 if h > 8 else 0
    _safe_addstr(s, py, w_t - len(p) - 2, p, curses.color_pair(CP_PAUSE) | curses.A_DIM)

class PlayerTracker:
    def __init__(self, bus):
        self.bus, self.last_pos, self.last_status, self.last_update = bus, 0.0, "Stopped", time.monotonic()
        self.poll_interval, self.last_poll = 0.2, 0.0
    def sync(self, force=False):
        now = time.monotonic()
        if force or (now - self.last_poll > self.poll_interval):
            info = mpris.get_player_info(self.bus)
            if info:
                st, pu, _ = info
                ap = pu / 1_000_000
                if force or st != "Playing" or self.last_status != "Playing": self.last_pos, self.last_update = ap, now
                else:
                    if abs(ap - (self.last_pos + (now - self.last_update))) > 1.0: self.last_pos, self.last_update = ap, now
                self.last_status, self.last_poll = st, now
            return True
        return False
    def get_pos(self):
        if self.last_status != "Playing": return self.last_pos
        return self.last_pos + (time.monotonic() - self.last_update)

def _check_song_changed(player_filter, title):
    try:
        t = mpris.get_now_playing(player_filter)
        return t and t["title"] != title
    except: return False

def run_focus(stdscr, synced, track_info, minimal=False):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(10)
    _init_colors()
    bus, title, artist, player = track_info["bus_name"], track_info["title"], track_info["artist"], track_info["player"]
    dur, prec = track_info["duration_us"] / 1_000_000, track_info.get("high_precision", False)
    tracker = PlayerTracker(bus)
    tracker.sync(force=True)
    last_word_idx, last_line_idx, last_ui_check = -1, -1, time.monotonic()
    h_m, w_m = stdscr.getmaxyx()
    particles = ParticleEngine(h_m, w_m)
    force_redraw = True
    last_line_text = ""

    while True:
        try: key = stdscr.getch()
        except: key = -1
        if key in (ord("q"), ord("Q"), 27): return "quit"
        if key == ord("m"): minimal = not minimal; force_redraw = True
        if key == ord("p"): particles.enabled = not particles.enabled; force_redraw = True
        if key == curses.KEY_RESIZE: force_redraw = True; stdscr.clear()
        
        tracker.sync()
        if tracker.last_status == "Stopped": return "stopped"
        pos, paused, now = tracker.get_pos(), tracker.last_status == "Paused", time.monotonic()
        if now - last_ui_check > 1.0:
            last_ui_check = now
            if _check_song_changed(player, title): return "song_changed"
        
        cur_l_idx = -1
        for i in range(len(synced)-1, -1, -1):
            if pos >= synced[i]["time"]: cur_l_idx = i; break
        
        cur_w_shown, cur_w_idx, full_txt = "♫", -1, " "
        if cur_l_idx >= 0:
            ld = synced[cur_l_idx]
            full_txt, syl = ld["text"], ld["syllables"]
            if syl:
                si = 0
                for j in range(len(syl)-1, -1, -1):
                    if pos >= syl[j]["time"]: si = j; break
                cur_w_shown, cur_w_idx = syl[si]["text"], si
        
        disp_w = cur_w_shown
        disp_l = full_txt if full_txt.strip() else last_line_text
        
        if force_redraw or cur_w_idx != last_word_idx or cur_l_idx != last_line_idx or (now % 0.05 < 0.02):
            force_redraw = False
            try:
                stdscr.erase()
                h, w = stdscr.getmaxyx()
                if h < 5 or w < 10: continue
                is_instr = (disp_w == "♫")
                particles.update(h, w)
                particles.draw(stdscr, intensity="mid" if is_instr else "low")
                if minimal:
                    if disp_w: _draw_big_word(stdscr, disp_w, h // 2, curses.color_pair(CP_ACCENT)|curses.A_BOLD)
                    if paused: _draw_pause_overlay(stdscr, disp_w, disp_l)
                else:
                    info = f"{'⏸' if paused else '♫'} {title}  ─  {artist}  [{player}]{'*' if prec else ''}"
                    _safe_addstr(stdscr, 0, _center_x(stdscr, info), info, curses.color_pair(CP_HEADER))
                    _safe_addstr(stdscr, 1, 1, "─"*(w-2), curses.color_pair(CP_DIM)|curses.A_DIM)
                    if disp_w:
                        _draw_big_word(stdscr, disp_w, h//2 - 1, curses.color_pair(CP_ACCENT)|curses.A_BOLD)
                        if disp_l.strip():
                            cy, cx = h//2 + 2, _center_x(stdscr, disp_l)
                            _safe_addstr(stdscr, cy, cx, disp_l, curses.color_pair(CP_DIM))
                            if cur_l_idx >= 0 and synced[cur_l_idx]["syllables"]:
                                syl = synced[cur_l_idx]["syllables"]
                                if 0 <= cur_w_idx < len(syl):
                                    before = " ".join([s["text"] for s in syl[:cur_w_idx]])
                                    hx = cx + len(before) + (1 if before else 0)
                                    _safe_addstr(stdscr, cy, hx, syl[cur_w_idx]["text"], curses.color_pair(CP_CURRENT)|curses.A_BOLD)
                    if h > 6: _draw_progress_bar(stdscr, h-2, pos, dur, paused)
                    if h > 4:
                        leg = "q quit  m minimal  p particles"
                        _safe_addstr(stdscr, h-1, _center_x(stdscr, leg), leg, curses.color_pair(CP_DIM)|curses.A_DIM)
                stdscr.refresh()
            except: pass
        last_line_idx, last_word_idx = cur_l_idx, cur_w_idx
        time.sleep(0.016)

def run_focus_plain(stdscr, plain, track_info, speed=1.0, minimal=False):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(10)
    _init_colors()
    bus, title, artist, player = track_info["bus_name"], track_info["title"], track_info["artist"], track_info["player"]
    dur = track_info["duration_us"] / 1_000_000
    words = []
    for l in plain:
        ws = l.split() if l.strip() else []
        if not ws: words.append(("", "", -1))
        else:
            for i, w in enumerate(ws): words.append((w, l, i))
    if not words: return "quit"
    wd = max(0.08, min(2.0/speed, (dur*0.8)/len(words))) if dur > 0 else 0.25/speed
    tracker = PlayerTracker(bus)
    tracker.sync(force=True)
    cur_wi, last_adv, last_ui = 0, time.monotonic(), time.monotonic()
    h_p, w_p = stdscr.getmaxyx()
    particles = ParticleEngine(h_p, w_p)
    force = True
    while cur_wi < len(words):
        try: k = stdscr.getch()
        except: k = -1
        if k in (ord("q"), ord("Q"), 27): return "quit"
        if k == ord("m"): minimal = not minimal; force = True
        if k == ord("p"): particles.enabled = not particles.enabled; force = True
        if k == curses.KEY_RESIZE: force = True; stdscr.clear()
        tracker.sync()
        if tracker.last_status == "Stopped": return "stopped"
        pos, paused, now = tracker.get_pos(), tracker.last_status == "Paused", time.monotonic()
        if now - last_ui > 1.0:
            last_ui = now
            if _check_song_changed(player, title): return "song_changed"
        if not paused:
            if now - last_adv > (wd if words[cur_wi][0] else wd*3): cur_wi += 1; last_adv = now; force = True
        if cur_wi >= len(words): break
        cw, fl, wil = words[cur_wi]
        if force or (now % 0.05 < 0.02):
            force = False
            try:
                stdscr.erase()
                h, w = stdscr.getmaxyx()
                if h < 5 or w < 10: continue
                particles.update(h, w)
                particles.draw(stdscr, intensity="mid" if not cw else "low")
                if minimal:
                    if cw: _draw_big_word(stdscr, cw, h//2)
                    if paused: _draw_pause_overlay(stdscr, cw, fl)
                else:
                    info = f"{'⏸' if paused else '♫'} {title}  ─  {artist} [{player}]"
                    _safe_addstr(stdscr, 0, _center_x(stdscr, info), info, curses.color_pair(CP_HEADER))
                    _safe_addstr(stdscr, 1, 1, "─"*(w-2), curses.color_pair(CP_DIM)|curses.A_DIM)
                    if cw:
                        _draw_big_word(stdscr, cw, h//2 - 1)
                        if fl.strip():
                            cy, cx = h//2 + 2, _center_x(stdscr, fl)
                            _safe_addstr(stdscr, cy, cx, fl, curses.color_pair(CP_DIM))
                            ws = fl.split()
                            if 0 <= wil < len(ws):
                                b = " ".join(ws[:wil])
                                _safe_addstr(stdscr, cy, cx + len(b) + (1 if b else 0), ws[wil], curses.color_pair(CP_CURRENT)|curses.A_BOLD)
                    if h > 6: _draw_progress_bar(stdscr, h-2, pos, dur, paused)
                    if h > 4: _safe_addstr(stdscr, h-1, _center_x(stdscr, "q quit  m minimal  p particles"), "q quit  m minimal  p particles", curses.color_pair(CP_DIM)|curses.A_DIM)
                stdscr.refresh()
            except: pass
        time.sleep(0.016)
    return "finished"

def run_synced(stdscr, synced, track_info):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(10)
    _init_colors()
    bus, title, artist, player = track_info["bus_name"], track_info["title"], track_info["artist"], track_info["player"]
    dur, prec = track_info["duration_us"] / 1_000_000, track_info.get("high_precision", False)
    tracker = PlayerTracker(bus)
    tracker.sync(force=True)
    cur_sc, last_ui = 0.0, time.monotonic()
    h_s, w_s = stdscr.getmaxyx()
    particles = ParticleEngine(h_s, w_s)
    while True:
        try: k = stdscr.getch()
        except: k = -1
        if k in (ord("q"), ord("Q"), 27): return "quit"
        if k == ord("p"): particles.enabled = not particles.enabled
        if k == curses.KEY_RESIZE: stdscr.clear()
        tracker.sync()
        if tracker.last_status == "Stopped": return "stopped"
        pos, paused, now = tracker.get_pos(), tracker.last_status == "Paused", time.monotonic()
        if now - last_ui > 1.0:
            last_ui = now
            if _check_song_changed(player, title): return "song_changed"
        cur_idx = -1
        for i in range(len(synced)-1, -1, -1):
            if pos >= synced[i]["time"]: cur_idx = i; break
        cur_sc += (float(cur_idx if cur_idx >= 0 else 0) - cur_sc) * 0.18
        try:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            if h < 6 or w < 10: continue
            particles.update(h, w)
            particles.draw(stdscr)
            hh = _draw_box_header(stdscr, title, artist, player, paused, precision=prec)
            top, bot = hh + 1, h - 3
            if bot - top < 3: stdscr.refresh(); continue
            cy = top + (bot - top) // 2
            for i, (ts, text) in enumerate([(l["time"], l["text"]) for l in synced]):
                dy = cy + int(i - cur_sc)
                if dy < top or dy >= bot: continue
                attr = curses.color_pair(CP_CURRENT)|curses.A_BOLD if i == cur_idx else curses.color_pair(CP_NEAR if abs(i-cur_idx)==1 else CP_FAR if abs(i-cur_idx)<=3 else CP_DIM)
                if not text.strip():
                    if i == cur_idx: _safe_addstr(stdscr, dy, _center_x(stdscr, "· · ·"), "· · ·", curses.color_pair(CP_INSTRUMENTAL))
                else: _safe_addstr(stdscr, dy, _center_x(stdscr, text), text, attr)
            if h > 4: _draw_progress_bar(stdscr, h - 2, pos, dur, paused)
            stdscr.refresh()
        except: pass
        time.sleep(0.016)

def run_waiting(stdscr, player_filter):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(500)
    _init_colors()
    h_w, w_w = stdscr.getmaxyx()
    particles = ParticleEngine(h_w, w_w)
    while True:
        try: k = stdscr.getch()
        except: k = -1
        if k in (ord("q"), ord("Q"), 27): return None
        if k == ord("p"): particles.enabled = not particles.enabled
        t = mpris.get_now_playing(player_filter)
        if t: return t
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        particles.update(h, w)
        particles.draw(stdscr)
        m = "♫  waiting for player..."
        _safe_addstr(stdscr, h//2, _center_x(stdscr, m), m, curses.color_pair(CP_DIM))
        stdscr.refresh()

def run_static(stdscr, lines, track_info, speed=1.0):
    curses.curs_set(0); stdscr.nodelay(True); stdscr.timeout(100); _init_colors()
    bus, title, artist, player = track_info["bus_name"], track_info["title"], track_info["artist"], track_info["player"]
    dur = track_info["duration_us"] / 1_000_000
    tracker = PlayerTracker(bus); tracker.sync(force=True)
    h_st, w_st = stdscr.getmaxyx()
    particles = ParticleEngine(h_st, w_st)
    while True:
        try: k = stdscr.getch()
        except: k = -1
        if k in (ord("q"), ord("Q"), 27): return "quit"
        if k == ord("p"): particles.enabled = not particles.enabled
        tracker.sync(); pos, paused = tracker.get_pos(), tracker.last_status == "Paused"
        if _check_song_changed(player, title): return "song_changed"
        idx = int((pos / dur) * len(lines)) if dur > 0 else 0
        idx = max(0, min(len(lines)-1, idx))
        try:
            stdscr.erase(); h, w = stdscr.getmaxyx()
            particles.update(h, w); particles.draw(stdscr)
            hh = _draw_box_header(stdscr, title, artist, player, paused)
            top, bot = hh + 1, h - 3
            cy = top + (bot - top) // 2
            for i, text in enumerate(lines):
                dy = cy + (i - idx)
                if dy < top or dy >= bot: continue
                attr = curses.color_pair(CP_CURRENT)|curses.A_BOLD if i == idx else curses.color_pair(CP_FAR)
                _safe_addstr(stdscr, dy, _center_x(stdscr, text), text, attr)
            if h > 4: _draw_progress_bar(stdscr, h - 2, pos, dur, paused)
            stdscr.refresh()
        except: pass
        time.sleep(0.05)

def show_fetching(stdscr, title, artist):
    _init_colors(); stdscr.erase(); h, w = stdscr.getmaxyx()
    m = f"fetching lyrics for {title}..."
    _safe_addstr(stdscr, h//2, _center_x(stdscr, m), m, curses.color_pair(CP_DIM))
    stdscr.refresh()

def run_no_lyrics(stdscr, track_info):
    curses.curs_set(0); stdscr.nodelay(True); stdscr.timeout(100); _init_colors()
    bus, title, artist = track_info["bus_name"], track_info["title"], track_info["artist"]
    dur = track_info["duration_us"] / 1_000_000
    last_check = time.monotonic()
    h_n, w_n = stdscr.getmaxyx()
    particles = ParticleEngine(h_n, w_n)
    while True:
        try: k = stdscr.getch()
        except: k = -1
        if k in (ord("q"), ord("Q"), 27): return "quit"
        if k == ord("p"): particles.enabled = not particles.enabled
        now = time.monotonic()
        try:
            status = mpris.get_playback_status(bus)
            pos_us = mpris.get_position_us(bus)
        except: return "player_closed"
        if status == "Stopped": return "stopped"
        pos_s = pos_us / 1_000_000
        if now - last_check > 1.5:
            last_check = now
            if _check_song_changed(player, title): return "song_changed"
        try:
            stdscr.erase(); h, w = stdscr.getmaxyx()
            particles.update(h, w); particles.draw(stdscr, intensity="mid")
            info = f"♫ {title}  ─  {artist}"
            _safe_addstr(stdscr, 0, _center_x(stdscr, info), info, curses.color_pair(CP_HEADER))
            msg = "no lyrics found"
            _safe_addstr(stdscr, h // 2, _center_x(stdscr, msg), msg, curses.color_pair(CP_DIM))
            hint = "waiting for next song..."
            _safe_addstr(stdscr, h // 2 + 2, _center_x(stdscr, hint), hint, curses.color_pair(CP_DIM) | curses.A_DIM)
            _draw_progress_bar(stdscr, h - 2, pos_s, dur)
            footer = "q quit  p particles  ─  liyri"
            _safe_addstr(stdscr, h - 1, _center_x(stdscr, footer), footer, curses.color_pair(CP_DIM) | curses.A_DIM)
            stdscr.refresh()
        except: pass
        time.sleep(0.05)
