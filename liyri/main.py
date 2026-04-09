import argparse
import curses
import sys

from liyri import __version__
from liyri import player as mpris
from liyri import lyrics as lyrics_api
from liyri import display
from liyri import config


def _list_players():
    players = mpris.get_active_players()
    if not players:
        print("  No MPRIS media players detected.")
        print("  Make sure a player is running (Spotify, VLC, browser, etc).")
        return

    print(f"\n  ♫  Detected MPRIS players ({len(players)}):\n")
    for bus_name, friendly in players:
        try:
            status = mpris.get_playback_status(bus_name)
        except Exception:
            status = "?"
        icon = {"Playing": "▶", "Paused": "⏸", "Stopped": "⏹"}.get(status, "?")
        print(f"    {icon}  {friendly}  ({status})")
    print()


def _fetch_for_track(track):
    title = track["title"]
    artist = track["artist"]
    album = track["album"]
    duration_s = track["duration_us"] / 1_000_000
    return lyrics_api.fetch_lyrics(title, artist, album, duration_s)


def _run_app(stdscr, args):
    mode = args.mode
    player_filter = args.player
    speed = args.speed
    no_sync = args.no_sync
    minimal = args.minimal

    while True:
        track = mpris.get_now_playing(player_filter)
        if not track:
            track = display.run_waiting(stdscr, player_filter)
            if track is None:
                return

        title = track["title"]
        artist = track["artist"]

        display.show_fetching(stdscr, title, artist)
        result = _fetch_for_track(track)

        use_synced = result and result["synced_lyrics"] and not no_sync
        has_plain = result and result["plain_lyrics"]

        if mode == "focus":
            if use_synced:
                ret = display.run_focus(stdscr, result["synced_lyrics"],
                                        track, minimal=minimal)
            elif has_plain:
                ret = display.run_focus_plain(stdscr, result["plain_lyrics"],
                                              track, speed=speed, minimal=minimal)
            else:
                ret = _run_no_lyrics(stdscr, track)
        elif mode == "scroll":
            if use_synced:
                ret = display.run_synced(stdscr, result["synced_lyrics"], track)
            elif has_plain:
                ret = display.run_static(stdscr, result["plain_lyrics"],
                                          track, speed=speed)
            else:
                ret = _run_no_lyrics(stdscr, track)
        else:
            ret = "quit"

        if ret == "quit":
            return
        elif ret == "song_changed":
            continue
        elif ret == "player_closed":
            continue
        elif ret == "stopped":
            continue
        elif ret == "finished":
            continue
        else:
            return


def _run_no_lyrics(stdscr, track_info):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)
    display._init_colors()

    bus_name = track_info["bus_name"]
    title = track_info["title"]
    artist = track_info["artist"]
    player_name = track_info["player"]
    duration_s = track_info["duration_us"] / 1_000_000

    import time
    last_check = time.monotonic()

    while True:
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1
        if key in (ord("q"), ord("Q"), 27):
            return "quit"

        now = time.monotonic()

        try:
            status = mpris.get_playback_status(bus_name)
            pos_us = mpris.get_position_us(bus_name)
        except Exception:
            return "player_closed"

        if status == "Stopped":
            return "stopped"

        pos_s = pos_us / 1_000_000

        if now - last_check > 1.5:
            last_check = now
            new_track = display._check_song_changed(bus_name, title)
            if new_track:
                return "song_changed"

        stdscr.erase()
        h, w = stdscr.getmaxyx()

        info = f"♫ {title}  ─  {artist}"
        display._safe_addstr(stdscr, 0, display._center_x(stdscr, info), info,
                             curses.color_pair(display.CP_HEADER))

        msg = "no lyrics found"
        display._safe_addstr(stdscr, h // 2, display._center_x(stdscr, msg), msg,
                             curses.color_pair(display.CP_DIM))

        hint = "waiting for next song..."
        display._safe_addstr(stdscr, h // 2 + 2, display._center_x(stdscr, hint), hint,
                             curses.color_pair(display.CP_DIM) | curses.A_DIM)

        display._draw_progress_bar(stdscr, h - 2, pos_s, duration_s)

        footer = "q quit  ─  liyri"
        display._safe_addstr(stdscr, h - 1, display._center_x(stdscr, footer), footer,
                             curses.color_pair(display.CP_DIM) | curses.A_DIM)

        stdscr.refresh()
        time.sleep(0.050)


def main():
    parser = argparse.ArgumentParser(
        prog="liyri",
        description="♫  Liyri — Animated terminal lyrics viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  liyri                    Focus mode (big word, default)\n"
            "  liyri --minimal          Focus mode, just the word\n"
            "  liyri --scroll           Scroll mode (full lyrics view)\n"
            "  liyri -p spotify         Use Spotify specifically\n"
            "  liyri --list-players     List detected media players\n"
        ),
    )
    parser.add_argument("--version", action="version",
                        version=f"liyri {__version__}")
    parser.add_argument("-p", "--player",
                        help="Target a specific MPRIS player by name")
    parser.add_argument("-s", "--speed", type=float, default=1.0,
                        help="Animation speed multiplier (default: 1.0)")
    parser.add_argument("--no-sync", action="store_true",
                        help="Force plain lyrics even if synced available")
    parser.add_argument("--list-players", action="store_true",
                        help="List detected MPRIS players and exit")
    parser.add_argument("--scroll", action="store_true",
                        help="Use scroll mode (full lyrics view)")
    parser.add_argument("--minimal", action="store_true",
                        help="Focus mode with just the word, no UI")

    args = parser.parse_args()

    cfg = config.load_config()

    if args.list_players:
        _list_players()
        sys.exit(0)

    mpris.ENABLE_STICKY_PLAYER = cfg.get("sticky_player", True)
    lyrics_api.ENABLE_KEYWORD_STRIPPING = cfg.get("strip_keywords", True)

    args.player = args.player if args.player else cfg.get("player", "")
    args.speed = args.speed if args.speed != 1.0 else cfg.get("speed", 1.0)
    args.no_sync = args.no_sync or cfg.get("no_sync", False)
    args.minimal = args.minimal or cfg.get("minimal", False)
    
    config_mode = cfg.get("mode", "focus")
    args.mode = "scroll" if (args.scroll or config_mode == "scroll") else "focus"

    try:
        curses.wrapper(lambda stdscr: _run_app(stdscr, args))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
