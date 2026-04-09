# ♫ Liyri-cli

**Liyri-cli** is a high-performance, minimal Linux CLI application that displays synchronized lyrics for currently playing media. It uses MPRIS D-Bus to instantly detect your player (Spotify, VLC, Chromium, etc.) and fetches lyrics from the LRCLIB API.

<details>
<summary><b> View Previews</b></summary>

<br>

**Focus mode**
<img width="1915" height="1078" alt="Focus Mode Preview" src="https://github.com/user-attachments/assets/d1e30076-9b86-458d-af73-942aa7ccff4f" />

**Scrolling mode**
<img width="1918" height="1077" alt="Scrolling Mode Preview" src="https://github.com/user-attachments/assets/66b18470-f853-4067-a449-1002858f969e" />

</details>

##  Quick Install

Install it globally so you can use it from anywhere:

```bash
git clone https://github.com/shxdnw/liyri-cli.git
cd liyri-cli
sudo ./install.sh
```

##  Usage

Simply run the app to instantly show lyrics for whatever is playing:

```bash
liyri
```

### Options

| Flag | Description |
|------|-------------|
| `--scroll` | Use full lyrics scroll mode instead of default big-word mode |
| `--minimal` | Hide window borders and player info to just focus on text |
| `-p PLAYER` | Target a specific player natively (e.g., `-p spotify`) |
| `-s SPEED` | Set animation speed multiplier (default: `1.0`) |
| `--no-sync` | Force fetch plain lyrics ignoring synchronized timelines |
| `--list-players`| Show all currently detected media players |

**Hotkeys:** 
- Press `m` to toggle minimal mode on the fly.
- Press `q` to quit.

##  Configuration

Liyri-cli supports advanced behavior toggles via a standard JSON configuration file located at `~/.config/liyri/config.json`. 

The app automatically generates this file with its defaults the first time you run it:

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

### Configuration Toggles
- **`mode`**: Choose between `"focus"` (default big-word mode) or `"scroll"` (full block-view mode).
- **`minimal`**: Hide window info and start cleanly (`true`/`false`).
- **`player`**: Restrict the lyrics engine to always track a specific player (e.g., `"spotify"`).
- **`strip_keywords`**: `true` automatically filters clutter tags like "(slowed)" or "nightcore" out of titles to help find correct lyrics when searches fail.
- **`sticky_player`**: `true` cleanly remembers the exact player you were listening to when you pause a track, rather than automatically jumping tracking logic to a nearby paused player. 

##  License
MIT
