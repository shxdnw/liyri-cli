import dbus

MPRIS_PREFIX = "org.mpris.MediaPlayer2."
MPRIS_PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"
DBUS_PROPS_IFACE = "org.freedesktop.DBus.Properties"

ENABLE_STICKY_PLAYER = True
_last_playing_bus = None

def _get_session_bus():
    return dbus.SessionBus()

def get_active_players():
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
    bus = _get_session_bus()
    proxy = bus.get_object(bus_name, "/org/mpris/MediaPlayer2")
    props = dbus.Interface(proxy, DBUS_PROPS_IFACE)
    return props

def get_playback_status(bus_name):
    props = _get_player_properties(bus_name)
    return str(props.Get(MPRIS_PLAYER_IFACE, "PlaybackStatus"))

def get_position_us(bus_name):
    props = _get_player_properties(bus_name)
    try:
        return int(props.Get(MPRIS_PLAYER_IFACE, "Position"))
    except dbus.exceptions.DBusException:
        return 0

def get_player_info(bus_name):
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

def _build_track(bus_name, friendly_name, status, metadata):
    title = str(metadata.get("xesam:title", ""))
    if not title:
        return None
    artists = metadata.get("xesam:artist", [])
    artist = str(artists[0]) if artists else ""
    album = str(metadata.get("xesam:album", ""))
    duration_us = int(metadata.get("mpris:length", 0))
    return {
        "bus_name": bus_name,
        "player": friendly_name,
        "title": title,
        "artist": artist,
        "album": album,
        "duration_us": duration_us,
        "status": status,
    }


def get_now_playing(player_name=None):
    global _last_playing_bus
    players = get_active_players()
    if not players:
        return None

    if player_name:
        player_name_lower = player_name.lower()
        players = [
            (bus, name) for bus, name in players
            if player_name_lower in name.lower()
        ]
        if not players:
            return None

    for bus_name, friendly_name in players:
        try:
            status, _, metadata = get_player_info(bus_name)
        except dbus.exceptions.DBusException:
            continue
        track = _build_track(bus_name, friendly_name, status, metadata)
        if not track:
            continue
        if status == "Playing":
            _last_playing_bus = bus_name
            return track

    if ENABLE_STICKY_PLAYER and _last_playing_bus:
        for bus_name, friendly_name in players:
            if bus_name == _last_playing_bus:
                try:
                    status, _, metadata = get_player_info(bus_name)
                except dbus.exceptions.DBusException:
                    continue
                track = _build_track(bus_name, friendly_name, status, metadata)
                if track:
                    return track

    for bus_name, friendly_name in players:
        try:
            status, _, metadata = get_player_info(bus_name)
        except dbus.exceptions.DBusException:
            continue
        track = _build_track(bus_name, friendly_name, status, metadata)
        if track:
            return track

    return None
