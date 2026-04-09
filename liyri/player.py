"""MPRIS D-Bus player detection — find and query currently playing media."""

import dbus


MPRIS_PREFIX = "org.mpris.MediaPlayer2."
MPRIS_PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"
DBUS_PROPS_IFACE = "org.freedesktop.DBus.Properties"

ENABLE_STICKY_PLAYER = True
_last_playing_bus = None


def _get_session_bus():
    """Return the session D-Bus."""
    return dbus.SessionBus()


def get_active_players():
    """Return a list of (bus_name, friendly_name) for all MPRIS players."""
    bus = _get_session_bus()
    names = bus.list_names()
    players = []
    for name in names:
        name = str(name)
        if name.startswith(MPRIS_PREFIX):
            friendly = name[len(MPRIS_PREFIX):]
            players.append((name, friendly))
    return players


def _get_player_properties(bus_name):
    """Read all Player properties from a given MPRIS bus name."""
    bus = _get_session_bus()
    proxy = bus.get_object(bus_name, "/org/mpris/MediaPlayer2")
    props = dbus.Interface(proxy, DBUS_PROPS_IFACE)
    return props


def get_playback_status(bus_name):
    """Return playback status string: 'Playing', 'Paused', or 'Stopped'."""
    props = _get_player_properties(bus_name)
    return str(props.Get(MPRIS_PLAYER_IFACE, "PlaybackStatus"))


def get_position_us(bus_name):
    """Return current playback position in microseconds."""
    props = _get_player_properties(bus_name)
    try:
        return int(props.Get(MPRIS_PLAYER_IFACE, "Position"))
    except dbus.exceptions.DBusException:
        return 0


def get_player_info(bus_name):
    """
    Get all player properties in one efficient D-Bus call.
    Returns (status, position_us, metadata)
    """
    props = _get_player_properties(bus_name)
    try:
        data = props.GetAll(MPRIS_PLAYER_IFACE)
        return (
            str(data.get("PlaybackStatus", "Stopped")),
            int(data.get("Position", 0)),
            data.get("Metadata", {})
        )
    except dbus.exceptions.DBusException:
        return "Stopped", 0, {}


def get_now_playing(player_name=None):
    """
    Detect the currently playing track.

    Args:
        player_name: Optional friendly name (e.g. 'spotify') to target
                     a specific player. If None, picks the first playing one.

    Returns:
        dict with keys: bus_name, player, title, artist, album, duration_us
        or None if nothing is playing.
    """
    global _last_playing_bus
    players = get_active_players()
    if not players:
        return None

    # If a specific player is requested, filter to it
    if player_name:
        player_name_lower = player_name.lower()
        players = [
            (bus, name) for bus, name in players
            if player_name_lower in name.lower()
        ]
        if not players:
            return None

    # Try to find a player that is actively playing
    for bus_name, friendly_name in players:
        try:
            status = get_playback_status(bus_name)
        except dbus.exceptions.DBusException:
            continue

        props = _get_player_properties(bus_name)
        try:
            metadata = props.Get(MPRIS_PLAYER_IFACE, "Metadata")
        except dbus.exceptions.DBusException:
            continue

        title = str(metadata.get("xesam:title", ""))
        artists = metadata.get("xesam:artist", [])
        if artists:
            artist = str(artists[0])
        else:
            artist = ""
        album = str(metadata.get("xesam:album", ""))
        duration_us = int(metadata.get("mpris:length", 0))

        if not title:
            continue

        # Prefer playing players, but return paused ones as fallback
        if status == "Playing":
            _last_playing_bus = bus_name
            return {
                "bus_name": bus_name,
                "player": friendly_name,
                "title": title,
                "artist": artist,
                "album": album,
                "duration_us": duration_us,
                "status": status,
            }

    # Fallback: prioritize the previously remembered playing bus to avoid jumping
    if ENABLE_STICKY_PLAYER and _last_playing_bus:
        for bus_name, friendly_name in players:
            if bus_name == _last_playing_bus:
                try:
                    props = _get_player_properties(bus_name)
                    metadata = props.Get(MPRIS_PLAYER_IFACE, "Metadata")
                    title = str(metadata.get("xesam:title", ""))
                    if title:
                        artists = metadata.get("xesam:artist", [])
                        artist = str(artists[0]) if artists else ""
                        album = str(metadata.get("xesam:album", ""))
                        duration_us = int(metadata.get("mpris:length", 0))
                        try:
                            status = get_playback_status(bus_name)
                        except dbus.exceptions.DBusException:
                            status = "Unknown"
                        return {
                            "bus_name": bus_name,
                            "player": friendly_name,
                            "title": title,
                            "artist": artist,
                            "album": album,
                            "duration_us": duration_us,
                            "status": status,
                        }
                except dbus.exceptions.DBusException:
                    pass

    # Fallback: return the first player with a title (even if paused)
    for bus_name, friendly_name in players:
        try:
            props = _get_player_properties(bus_name)
            metadata = props.Get(MPRIS_PLAYER_IFACE, "Metadata")
        except dbus.exceptions.DBusException:
            continue
        title = str(metadata.get("xesam:title", ""))
        if title:
            artists = metadata.get("xesam:artist", [])
            artist = str(artists[0]) if artists else ""
            album = str(metadata.get("xesam:album", ""))
            duration_us = int(metadata.get("mpris:length", 0))
            try:
                status = get_playback_status(bus_name)
            except dbus.exceptions.DBusException:
                status = "Unknown"
            return {
                "bus_name": bus_name,
                "player": friendly_name,
                "title": title,
                "artist": artist,
                "album": album,
                "duration_us": duration_us,
                "status": status,
            }

    return None
