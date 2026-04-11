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
        
        if result:
            track["high_precision"] = result.get("high_precision", False)

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
                ret = display.run_no_lyrics(stdscr, track)
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
