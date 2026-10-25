#!/bin/sh
# skills-hub installer for Linux and macOS.
#
# The same four steps as install.ps1: find Python, fetch the hub, hand off.
# Every write happens in bootstrap.py.
#
#   curl -fsSL https://raw.githubusercontent.com/khan2abdul/skills-hub/main/install.sh | sh

set -eu

HUB_URL="https://github.com/khan2abdul/skills-hub/archive/refs/heads/main.tar.gz"
HUB_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/skills-hub"

step() { printf '  \033[36m%s\033[0m\n' "$1"; }
warn() { printf '  \033[33m%s\033[0m\n' "$1"; }
bad()  { printf '  \033[31m%s\033[0m\n' "$1" >&2; }

# 1. Python 3.11 or newer.
find_python() {
    for exe in python3 python; do
        if command -v "$exe" >/dev/null 2>&1; then
            if "$exe" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
                PY="$exe"
                return 0
            fi
        fi
    done
    return 1
}

# 2. Ask before installing anything. No sudo, no system package manager.
add_python() {
    bad 'Python 3.11+ is missing.'
    if command -v brew >/dev/null 2>&1; then
        warn 'Homebrew can install it.'
        # The documented path is `curl ... | sh`, so stdin is this script and a
        # plain `read` would eat the lines below it. Ask on the terminal instead.
        if [ -t 0 ]; then
            printf '  Install Python 3.12 with Homebrew now? [y/N] '
            read -r answer || answer=n
        elif [ -r /dev/tty ]; then
            printf '  Install Python 3.12 with Homebrew now? [y/N] ' > /dev/tty
            read -r answer < /dev/tty || answer=n
        else
            warn 'No terminal to ask on. Install Python 3.11+ and run this again.'
            exit 1
        fi
        case "$answer" in
            y|Y|yes|YES) brew install python ;;
            *) warn 'Nothing was installed.'; exit 1 ;;
        esac
        return
    fi
    if command -v apt-get >/dev/null 2>&1; then
        warn 'Install Python 3.11+ with your package manager, then run this again:'
        warn '  sudo apt-get install -y python3'
    elif command -v dnf >/dev/null 2>&1; then
        warn '  sudo dnf install -y python3'
    elif command -v pacman >/dev/null 2>&1; then
        warn '  sudo pacman -S --needed python'
    else
        warn 'Install Python 3.11+ from https://www.python.org/downloads/'
    fi
    exit 1
}

# 3. The hub, unpacked once. A re-run reuses it.
get_hub() {
    if [ -f "$HUB_DIR/tools/bootstrap.py" ]; then
        step "Hub already at $HUB_DIR"
        return
    fi
    step "Downloading the hub to $HUB_DIR"
    tmp="$(mktemp -d)"
    # A failed download must leave no half hub behind, so unpack into tmp first.
    trap 'rm -rf "$tmp"' EXIT
    if ! curl -fsSL "$HUB_URL" -o "$tmp/hub.tar.gz"; then
        bad 'Download failed.'
        exit 1
    fi
    if ! tar -xzf "$tmp/hub.tar.gz" -C "$tmp"; then
        bad 'Unpack failed.'
        exit 1
    fi
    mkdir -p "$HUB_DIR"
    inner="$(find "$tmp" -maxdepth 1 -mindepth 1 -type d | head -n 1)"
    cp -R "$inner"/. "$HUB_DIR"/
    if [ ! -f "$HUB_DIR/tools/bootstrap.py" ]; then
        bad "The hub is incomplete at $HUB_DIR"
        exit 1
    fi
}

printf '\n\033[37mskills-hub\033[0m\n'
printf '\033[90m42 skills and one writing style for your AI tools.\033[0m\n\n'

PY=""
if ! find_python; then
    add_python
    if ! find_python; then
        bad 'Python is still missing. Open a new terminal and run this again.'
        exit 1
    fi
fi
step "Python $("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])') found"

get_hub

# 4. The one hand-off.
exec "$PY" "$HUB_DIR/tools/bootstrap.py" "$@"
