import argparse
import curses
import sys
import time
import threading

from liyri import __version__
from liyri import player as mpris
from liyri import lyrics as lyrics_api
from liyri import display
from liyri import config


def _prefetch_loop(player_filter):
    last_title = None
    while True:
        time.sleep(2)
        try:
            track = mpris.get_now_playing(player_filter)
            if track and track["title"] != last_title:
                last_title = track["title"]
                lyrics_api.fetch_lyrics(track["title"], track["artist"],
                                        track["album"], track["duration_us"] / 1_000_000)
        except Exception:
            pass


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


def _run_search(stdscr, title, artist):
    display.show_fetching(stdscr, title, artist)
    result = lyrics_api.fetch_lyrics(title, artist)
    if result and (result["synced_lyrics"] or result["plain_lyrics"]):
        display.run_search_viewer(stdscr, result, title, artist)
    else:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        msg = f"no lyrics found for \"{title}\""
        stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)
        stdscr.addstr(h // 2 + 1, max(0, (w - len("press any key to exit")) // 2), "press any key to exit")
        stdscr.getch()


def _run_app(stdscr, args):
    mode = args.mode
    player_filter = args.player
    speed = args.speed
    no_sync = [args.no_sync]
    minimal = args.minimal

    prefetcher = threading.Thread(target=_prefetch_loop, args=(player_filter,), daemon=True)
    prefetcher.start()

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

        if result:
            track["high_precision"] = result.get("high_precision", False)
            track["cached"] = result.get("cached", False)

        use_synced = result and result["synced_lyrics"] and not no_sync[0]
        has_plain = result and result["plain_lyrics"]

        if mode == "focus":
            if use_synced:
                ret = display.run_focus(stdscr, result["synced_lyrics"],
                                        track, minimal=minimal, no_sync=no_sync)
            elif has_plain:
                ret = display.run_focus_plain(stdscr, result["plain_lyrics"],
                                              track, speed=speed, minimal=minimal, no_sync=no_sync)
            else:
                ret = display.run_no_lyrics(stdscr, track)
        elif mode == "scroll":
            if use_synced:
                ret = display.run_synced(stdscr, result["synced_lyrics"], track, no_sync=no_sync)
            elif has_plain:
                ret = display.run_static(stdscr, result["plain_lyrics"],
                                          track, speed=speed, no_sync=no_sync)
            else:
                ret = display.run_no_lyrics(stdscr, track)
        else:
            ret = "quit"

        if ret in ("quit", None):
            return
        continue


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
    parser.add_argument("--search", type=str, metavar="\"ARTIST - TITLE\"",
                        help="Search lyrics for a song without playing it")
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

    if args.search:
        parts = args.search.split(" - ", 1)
        artist = parts[0].strip() if len(parts) == 2 else ""
        title = parts[1].strip() if len(parts) == 2 else args.search.strip()
        curses.wrapper(lambda stdscr: _run_search(stdscr, title, artist))
        sys.exit(0)

    display.set_theme(cfg.get("theme", "default"))
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
