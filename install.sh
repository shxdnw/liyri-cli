#!/bin/bash
# Install liyri as a system-wide command
# This creates a symlink in /usr/local/bin so you can run `liyri` from anywhere

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER="/usr/local/bin/liyri"

echo "♫  Installing liyri..."

# Check dependencies
python3 -c "import dbus, requests, thefuzz" 2>/dev/null || {
    echo "Error: Missing Python dependencies."
    echo "Install them with:"
    echo "  sudo pacman -S python-dbus python-requests python-thefuzz python-levenshtein   # Arch"
    echo "  sudo apt install python3-dbus python3-requests python3-thefuzz python3-levenshtein # Debian/Ubuntu"
    echo "  pip install dbus-python requests thefuzz python-Levenshtein                      # Generic PIP"
    exit 1
}

# Create wrapper script
sudo tee "$WRAPPER" > /dev/null << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
exec python3 -m liyri "\$@"
EOF

sudo chmod +x "$WRAPPER"

echo "✓  Installed! Run 'liyri' from anywhere."
echo "   liyri                  — show lyrics for current song"
echo "   liyri --list-players   — list detected players"
echo "   liyri --help           — show all options"
