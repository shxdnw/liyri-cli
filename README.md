# ♫ Liyri-cli

**Liyri-cli** is a high-performance, minimal Linux CLI application that displays synchronized lyrics for currently playing media. It uses MPRIS D-Bus to detect your player (Spotify, VLC, browser, etc.) and fetches lyrics from the LRCLIB API.

![Liyri Preview](https://github.com/user-attachments/assets/placeholder)

## ✨ Features

- **Focus Mode**: Large, centered block-letter ASCII animation showing one word at a time.
- **Scroll Mode**: Classic full-lyrics view with smooth scrolling.
- **Silky Smooth Sync**: High-precision position interpolation (60fps) for perfectly timed lyrics without D-Bus lag.
- **Multi-Language Support**: Renders Cyrillic, CJK (Chinese, Japanese, Korean), and other non-Latin characters gracefully.
- **Minimal Mode**: Toggle UI elements with `m` to focus only on the lyrics.
- **Automatic Song Detection**: Real-time monitoring of song changes, pauses, and skips.
- **Lyrics Caching**: In-memory cache for instantaneous loading of previously fetched songs.

## 🚀 Installation

### Prerequisites

- Python 3.8+
- A Linux system with a running MPRIS-compatible media player (Spotify, VLC, MPD, Chrome, etc.)
- System dependencies (usually pre-installed on most distros):
  ```bash
  # Arch Linux
  sudo pacman -S python-dbus
  
  # Ubuntu/Debian
  sudo apt install python3-dbus
  ```

### Quick Install (Standalone)

Clone the repo and run the install script:

```bash
git clone https://github.com/shxdnw/liyri-cli.git
cd liyri-cli
sudo ./install.sh
```
This will symlink the liyri command to `/usr/local/bin/liyri`.

### Manual Install (Virtual Environment)

```bash
git clone https://github.com/shxdnw/liyri-cli.git
cd liyri-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 🎮 Usage

Run `liyri` to start the focus mode:

```bash
liyri
```

### Options

| Flag | Description |
|------|-------------|
| `--minimal` | Start in minimal mode (just the big words) |
| `--scroll` | Use full lyrics scroll mode |
| `-p PLAYER` | Target a specific player (e.g., `-p spotify`) |
| `--list-players`| Show all detected media players |

### Hotkeys

- `m`: Toggle minimal mode
- `q` or `Esc`: Quit

## ⚙️ Configuration

Liyri-cli is designed to be zero-config. It automatically picks the best available synchronized lyrics and handles player detection out of the box.

## 📄 License

MIT
