#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER="/usr/local/bin/liyri"

detect_distro() {
    if [ -f /etc/arch-release ]; then
        echo "arch"
    elif grep -qi "ubuntu\|debian\|mint\|pop" /etc/os-release 2>/dev/null; then
        echo "debian"
    elif grep -qi "fedora" /etc/os-release 2>/dev/null; then
        echo "fedora"
    elif grep -qi "opensuse\|suse" /etc/os-release 2>/dev/null; then
        echo "suse"
    else
        echo "unknown"
    fi
}

install_deps() {
    local distro="$1"
    case "$distro" in
        arch)
            echo "→ Detected Arch Linux — using pacman"
            sudo pacman -S --needed python-dbus python-requests
            ;;
        debian)
            echo "→ Detected Debian/Ubuntu — using apt"
            sudo apt install -y python3-dbus python3-requests
            ;;
        fedora)
            echo "→ Detected Fedora — using dnf"
            sudo dnf install -y python3-dbus python3-requests
            ;;
        suse)
            echo "→ Detected openSUSE — using zypper"
            sudo zypper install -y python3-dbus python3-requests
            ;;
        *)
            echo "→ Unknown distro — trying pip"
            pip3 install --user dbus-python requests
            ;;
    esac
}

echo "♫  Installing liyri..."

DISTRO=$(detect_distro)

if python3 -c "import dbus, requests" 2>/dev/null; then
    echo "✓  Python dependencies already satisfied"
else
    echo "→ Installing missing dependencies..."
    install_deps "$DISTRO"
fi

sudo tee "$WRAPPER" > /dev/null << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
exec python3 -m liyri "\$@"
EOF

sudo chmod +x "$WRAPPER"

echo "✓  Installed! Run 'liyri' from anywhere."
echo "   liyri                  — show lyrics for current song"
echo "   liyri --list-players   — list detected players"
echo "   liyri --search \"...\"   — look up a song"
echo "   liyri --help           — show all options"
