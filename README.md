# ♫ Liyri-cli

A minimal Linux CLI app that displays synchronized lyrics for whatever you're currently playing, uses MPRIS D-Bus and the LRCLIB API.

Supports Spotify, VLC, Chromium, and any other MPRIS-compatible player out of the box.

<img width="900" alt="Focus Mode Preview" src="https://github.com/user-attachments/assets/d1e30076-9b86-458d-af73-942aa7ccff4f" />

<details>
<summary><b>Scrolling mode preview</b></summary>
<br>
<img width="900" alt="Scrolling Mode Preview" src="https://github.com/user-attachments/assets/66b18470-f853-4067-a449-1002858f969e" />
</details>

---

## Install

**Requirements:** Python 3.8+, a running MPRIS-compatible media player

Install dependencies and the app globally:

```bash
pip install dbus-python requests thefuzz python-Levenshtein
git clone https://github.com/shxdnw/liyri-cli.git
cd liyri-cli
sudo ./install.sh
```

> **Note:** `dbus-python` may require system packages on some distros.  
> Arch: `sudo pacman -S python-dbus`  
> Debian/Ubuntu: `sudo apt install python3-dbus`

---

## Usage

Run from anywhere once installed:

```bash
liyri
```

### Flags

| Flag | Description |
|------|-------------|
| `--scroll` | Full lyrics scroll mode instead of default focus mode |
| `--minimal` | Hide borders and player info |
| `-p PLAYER` | Target a specific player (e.g. `-p spotify`) |
| `-s SPEED` | Animation speed multiplier (default: `1.0`) |
| `--no-sync` | Fetch plain lyrics, ignore sync timelines |
| `--list-players` | List all detected media players |

### Hotkeys

| Key | Action |
|-----|--------|
| `m` | Toggle minimal mode |
| `p` | Toggle particles |
| `q` | Quit |

---

## Configuration

Config is auto-generated on first run at `~/.config/liyri/config.json`:

```json
{
    "mode": "focus",
    "minimal": false,
    "player": "",
    "speed": 1.0,
    "no_sync": false,
    "strip_keywords": true,
    "sticky_player": true
}
```

| Key | Description |
|-----|-------------|
| `mode` | `"focus"` for big-word mode, `"scroll"` for full block view |
| `minimal` | Start without borders or player info |
| `player` | Lock tracking to a specific player (e.g. `"spotify"`) |
| `speed` | Animation speed multiplier |
| `no_sync` | Always fetch plain lyrics |
| `strip_keywords` | Strip tags like "(slowed)" or "nightcore" for better lyric matching |
| `sticky_player` | Remember the last active player on pause instead of jumping to another |

---

## License

MIT