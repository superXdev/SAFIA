#!/usr/bin/env bash
# ============================================================================
# SAFIA Installer — Linux & macOS
# ============================================================================
# Installs the SAFIA Telegram bot as a background daemon with auto-start.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/superXdev/SAFIA/main/install.sh | bash
#
# Or with options:
#   curl -fsSL ... | bash -s -- --skip-setup --branch develop
# ============================================================================

set -e

if [ -n "${PYTHONPATH:-}" ]; then
    echo "⚠ Ignoring inherited PYTHONPATH during install"
    unset PYTHONPATH
fi
if [ -n "${PYTHONHOME:-}" ]; then
    echo "⚠ Ignoring inherited PYTHONHOME during install"
    unset PYTHONHOME
fi

export UV_NO_CONFIG=1

# ── Colors ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# ── Configuration ───────────────────────────────────────────────────────────
REPO_URL_SSH="git@github.com:superXdev/SAFIA.git"
REPO_URL_HTTPS="https://github.com/superXdev/SAFIA.git"
SAFIA_HOME="${SAFIA_HOME:-$HOME/.safia}"
if [ -n "${SAFIA_INSTALL_DIR:-}" ]; then
    INSTALL_DIR="$SAFIA_INSTALL_DIR"
    INSTALL_DIR_EXPLICIT=true
else
    INSTALL_DIR=""
    INSTALL_DIR_EXPLICIT=false
fi
PYTHON_VERSION="3.12"

USE_VENV=true
BRANCH="main"
NON_INTERACTIVE=false

# ── Parse arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-venv)
            USE_VENV=false
            shift
            ;;
        --branch|-b)
            BRANCH="$2"
            shift 2
            ;;
        --dir)
            INSTALL_DIR="$2"
            INSTALL_DIR_EXPLICIT=true
            shift 2
            ;;
        --safia-home)
            SAFIA_HOME="$2"
            shift 2
            ;;
        --non-interactive)
            NON_INTERACTIVE=true
            shift
            ;;
        -h|--help)
            echo "SAFIA Installer"
            echo ""
            echo "Usage: install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-venv          Skip dependency install"
            echo "  --branch NAME      Git branch to install (default: main)"
            echo "  --dir PATH         Custom install directory (default: ~/.safia/safia)"
            echo "  --safia-home PATH  Data/config directory (default: ~/.safia)"
            echo "  --non-interactive  Skip prompts that require user input"
            echo "  -h, --help         Show this help"
            echo ""
            echo "After install, use the 'safia' command:"
            echo "  safia setup      Re-run setup wizard"
            echo "  safia config     Edit configuration"
            echo "  safia access     Manage bot access control"
            echo "  safia start      Start the bot daemon"
            echo "  safia stop       Stop the bot daemon"
            echo "  safia restart    Restart the bot daemon"
            echo "  safia status     Show daemon status"
            echo "  safia logs       Show recent logs"
            echo "  safia test       Run tests"
            echo "  safia update     Update and restart"
            echo "  safia uninstall  Remove SAFIA completely"
            exit 0
            ;;
        *)
            SAFIA_SUBCMDS="setup config access start stop restart status logs test update uninstall"
            for _cmd in $SAFIA_SUBCMDS; do
                if [ "$1" = "$_cmd" ]; then
                    if [ -x "$HOME/.local/bin/safia" ]; then
                        exec "$HOME/.local/bin/safia" "$@"
                    fi
                    echo "SAFIA is not installed yet. Run without arguments to install first:"
                    echo "  $0"
                    exit 1
                fi
            done
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage."
            exit 1
            ;;
    esac
done

# ── Helpers ─────────────────────────────────────────────────────────────────

print_banner() {
    echo ""
    echo -e "${MAGENTA}${BOLD}"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│    ███████╗ █████╗ ███████╗██╗ █████╗                   │"
    echo "│    ██╔════╝██╔══██╗██╔════╝██║██╔══██╗                  │"
    echo "│    ███████╗███████║█████╗  ██║███████║                  │"
    echo "│    ╚════██║██╔══██║██╔══╝  ██║██╔══██║                  │"
    echo "│    ███████║██║  ██║██║     ██║██║  ██║                  │"
    echo "│    ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝                  │"
    echo "├─────────────────────────────────────────────────────────┤"
    echo "│   AI-Powered Personal Finance Assistant — Telegram Bot  │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

log_info()    { echo -e "${CYAN}→${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
log_error()   { echo -e "${RED}✗${NC} $1"; }

prompt_yes_no() {
    local question="$1"
    local default="${2:-yes}"
    local prompt_suffix

    case "$default" in
        [yY]|[yY][eE][sS]|1) prompt_suffix="[Y/n]" ;;
        *) prompt_suffix="[y/N]" ;;
    esac

    if [ "$NON_INTERACTIVE" = true ]; then
        case "$default" in
            [yY]|[yY][eE][sS]|1) return 0 ;;
            *) return 1 ;;
        esac
    fi

    if [ ! -t 0 ] && [ ! -t 1 ]; then
        if [ -r /dev/tty ] && [ -w /dev/tty ]; then
            printf "%s %s " "$question" "$prompt_suffix" > /dev/tty
            IFS= read -r answer < /dev/tty || answer=""
        else
            case "$default" in
                [yY]|[yY][eE][sS]|1) return 0 ;;
                *) return 1 ;;
            esac
        fi
    else
        printf "%s %s " "$question" "$prompt_suffix"
        IFS= read -r answer || answer=""
    fi

    answer="${answer#"${answer%%[![:space:]]*}"}"
    answer="${answer%"${answer##*[![:space:]]}"}"

    if [ -z "$answer" ]; then
        case "$default" in
            [yY]|[yY][eE][sS]|1) return 0 ;;
            *) return 1 ;;
        esac
    fi

    case "$answer" in
        [yY]|[yY][eE][sS]) return 0 ;;
        *) return 1 ;;
    esac
}

# ── OS Detection ────────────────────────────────────────────────────────────

detect_os() {
    case "$(uname -s)" in
        Linux*)  OS="linux";  DISTRO="unknown"
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO="$ID"
            fi
            ;;
        Darwin*) OS="macos";  DISTRO="macos" ;;
        *)
            log_error "Unsupported operating system: $(uname -s)"
            log_info "SAFIA currently supports Linux and macOS."
            exit 1
            ;;
    esac
    log_success "Detected: $OS ($DISTRO)"
}

# ── Resolve install layout ──────────────────────────────────────────────────

resolve_install_layout() {
    if [ "$INSTALL_DIR_EXPLICIT" = true ]; then
        log_info "Install directory: $INSTALL_DIR (explicit)"
        return 0
    fi
    INSTALL_DIR="$SAFIA_HOME/safia"
}

get_bin_dir() {
    echo "$HOME/.local/bin"
}

# ── Git ─────────────────────────────────────────────────────────────────────

attempt_install_git() {
    case "$OS" in
        macos)
            if command -v brew >/dev/null 2>&1; then
                log_info "Installing Git via Homebrew..."
                brew install git >/dev/null 2>&1 || true
                command -v git >/dev/null 2>&1 && return 0
            fi
            if command -v xcode-select >/dev/null 2>&1; then
                log_info "Requesting Apple Command Line Tools (provides git)..."
                log_info "If a macOS dialog appears, click \"Install\"."
                xcode-select --install >/dev/null 2>&1 || true
                local waited=0
                while [ "$waited" -lt 600 ]; do
                    if command -v git >/dev/null 2>&1 && git --version >/dev/null 2>&1; then
                        return 0
                    fi
                    sleep 5
                    waited=$((waited + 5))
                done
            fi
            return 1
            ;;
        linux)
            local sudo_cmd=""
            command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null && sudo_cmd="sudo"
            case "$DISTRO" in
                ubuntu|debian)
                    log_info "Installing Git via apt..."
                    $sudo_cmd apt-get update -qq >/dev/null 2>&1 || true
                    $sudo_cmd apt-get install -y -qq git >/dev/null 2>&1 || true
                    ;;
                fedora)
                    log_info "Installing Git via dnf..."
                    $sudo_cmd dnf install -y git >/dev/null 2>&1 || true
                    ;;
                arch)
                    log_info "Installing Git via pacman..."
                    $sudo_cmd pacman -S --noconfirm git >/dev/null 2>&1 || true
                    ;;
                *) return 1 ;;
            esac
            command -v git >/dev/null 2>&1 && return 0
            return 1
            ;;
    esac
    return 1
}

check_git() {
    log_info "Checking Git..."
    if command -v git &>/dev/null && git --version &>/dev/null; then
        GIT_VERSION=$(git --version | awk '{print $3}')
        log_success "Git $GIT_VERSION found"
        return 0
    fi

    log_warn "Git not found — attempting automatic install..."
    if attempt_install_git; then
        GIT_VERSION=$(git --version | awk '{print $3}')
        log_success "Git $GIT_VERSION installed"
        return 0
    fi

    log_error "Could not install Git automatically. Please install it manually:"
    case "$OS" in
        macos) log_info "  brew install git" ;;
        linux)
            case "$DISTRO" in
                ubuntu|debian) log_info "  sudo apt install git" ;;
                fedora)        log_info "  sudo dnf install git" ;;
                arch)          log_info "  sudo pacman -S git" ;;
                *)             log_info "  Use your package manager to install git" ;;
            esac
            ;;
    esac
    exit 1
}

# ── uv ──────────────────────────────────────────────────────────────────────

install_uv() {
    local _managed_uv="$SAFIA_HOME/bin/uv"

    if [ -x "$_managed_uv" ]; then
        UV_CMD="$_managed_uv"
        UV_VERSION=$($UV_CMD --version 2>/dev/null || echo "unknown")
        log_success "uv found ($UV_VERSION)"
        return 0
    fi

    if command -v uv >/dev/null 2>&1; then
        UV_CMD="$(command -v uv)"
        UV_VERSION=$($UV_CMD --version 2>/dev/null || echo "unknown")
        log_success "uv found ($UV_VERSION)"
        return 0
    fi

    log_info "Installing uv..."
    mkdir -p "$SAFIA_HOME/bin"

    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | UV_UNMANAGED_INSTALL="$SAFIA_HOME/bin" sh >/dev/null 2>&1
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | UV_UNMANAGED_INSTALL="$SAFIA_HOME/bin" sh >/dev/null 2>&1
    else
        log_error "Neither curl nor wget found. Please install one of them and re-run."
        exit 1
    fi

    if [ -x "$_managed_uv" ]; then
        UV_CMD="$_managed_uv"
        UV_VERSION=$($UV_CMD --version 2>/dev/null || echo "unknown")
        log_success "uv installed ($UV_VERSION)"
    else
        log_error "uv installation failed."
        log_info "Install manually: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
}

# ── Python ──────────────────────────────────────────────────────────────────

check_python() {
    log_info "Checking Python $PYTHON_VERSION..."
    if PYTHON_PATH="$("$UV_CMD" python find "$PYTHON_VERSION" 2>/dev/null)"; then
        PYTHON_FOUND_VERSION="$("$PYTHON_PATH" --version 2>/dev/null)"
        log_success "Python found: $PYTHON_FOUND_VERSION"
        return 0
    fi

    log_info "Python $PYTHON_VERSION not found — installing via uv..."
    if "$UV_CMD" python install "$PYTHON_VERSION"; then
        PYTHON_PATH="$("$UV_CMD" python find "$PYTHON_VERSION")"
        PYTHON_FOUND_VERSION="$("$PYTHON_PATH" --version 2>/dev/null)"
        log_success "Python installed: $PYTHON_FOUND_VERSION"
    else
        log_error "Failed to install Python $PYTHON_VERSION"
        exit 1
    fi
}

# ── Clone / update ──────────────────────────────────────────────────────────

clone_repo() {
    log_info "Installing to $INSTALL_DIR..."

    if [ -d "$INSTALL_DIR/.git" ] && ! git -C "$INSTALL_DIR" rev-parse --verify HEAD >/dev/null 2>&1; then
        log_warn "Broken checkout detected, removing..."
        rm -rf "$INSTALL_DIR"
    fi

    if [ -d "$INSTALL_DIR" ]; then
        if [ -d "$INSTALL_DIR/.git" ]; then
            log_info "Existing installation found — updating..."
            cd "$INSTALL_DIR"
            git fetch origin "$BRANCH"
            git checkout "$BRANCH"
            git pull --ff-only origin "$BRANCH"
        else
            log_error "Directory exists but is not a git repository: $INSTALL_DIR"
            log_info "Remove it or use --dir to choose a different location."
            exit 1
        fi
    else
        log_info "Cloning repository..."
        if GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=5" \
           git clone --depth 1 --branch "$BRANCH" "$REPO_URL_SSH" "$INSTALL_DIR" 2>/dev/null; then
            log_success "Cloned via SSH"
        else
            rm -rf "$INSTALL_DIR" 2>/dev/null
            log_info "SSH failed, trying HTTPS..."
            if git clone --depth 1 --branch "$BRANCH" "$REPO_URL_HTTPS" "$INSTALL_DIR"; then
                log_success "Cloned via HTTPS"
            else
                log_error "Failed to clone repository."
                exit 1
            fi
        fi
    fi

    cd "$INSTALL_DIR"
    log_success "Repository ready at $INSTALL_DIR"
}

# ── Install dependencies ────────────────────────────────────────────────────

install_deps() {
    if [ "$USE_VENV" = false ]; then
        log_info "Skipping dependency install (--no-venv)"
        return 0
    fi

    log_info "Installing Python dependencies with uv..."
    cd "$INSTALL_DIR"
    "$UV_CMD" sync
    log_success "Dependencies installed"
}

# ── Daemon control helpers (for CLI wrapper) ────────────────────────────────

generate_daemon_control_functions() {
    case "$OS" in
        linux)
            cat << 'DAEMON_LINUX'
safia_start() {
    local service_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
    local svc_bot="$service_dir/safia.service"
    local svc_admin="$service_dir/safia-admin.service"

    if [ ! -f "$INSTALL_DIR/.env" ]; then
        echo "✗ No .env found. Run 'safia setup' first to configure."
        return 1
    fi

    if [ ! -f "$svc_bot" ] || [ ! -f "$svc_admin" ]; then
        mkdir -p "$service_dir"
        mkdir -p "$SAFIA_HOME/logs"
    fi

    if [ ! -f "$svc_bot" ]; then
        cat > "$svc_bot" << 'SVC'
[Unit]
Description=SAFIA Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=__INSTALL_DIR__
ExecStart=__INSTALL_DIR__/.venv/bin/python main.py
Restart=always
RestartSec=15
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:__SAFIA_HOME__/logs/bot.log
StandardError=append:__SAFIA_HOME__/logs/bot.log

[Install]
WantedBy=default.target
SVC
        sed -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" -e "s|__SAFIA_HOME__|$SAFIA_HOME|g" "$svc_bot" > "${svc_bot}.tmp" && mv "${svc_bot}.tmp" "$svc_bot"
    fi

    if [ ! -f "$svc_admin" ]; then
        cat > "$svc_admin" << 'SVC'
[Unit]
Description=SAFIA Admin Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=__INSTALL_DIR__
ExecStart=__INSTALL_DIR__/.venv/bin/python admin_dashboard.py
Restart=always
RestartSec=15
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:__SAFIA_HOME__/logs/admin.log
StandardError=append:__SAFIA_HOME__/logs/admin.log

[Install]
WantedBy=default.target
SVC
        sed -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" -e "s|__SAFIA_HOME__|$SAFIA_HOME|g" "$svc_admin" > "${svc_admin}.tmp" && mv "${svc_admin}.tmp" "$svc_admin"
        systemctl --user daemon-reload
        systemctl --user enable safia.service safia-admin.service
        echo "→ Daemon configured (auto-start on boot enabled)."
    fi

    systemctl --user start safia.service safia-admin.service 2>/dev/null && \
        echo "✓ SAFIA started (bot + admin dashboard on http://127.0.0.1:5454)." || \
        echo "✗ Failed to start. Check: systemctl --user status safia"
}

safia_stop() {
    systemctl --user stop safia.service safia-admin.service 2>/dev/null && \
        echo "✓ SAFIA stopped." || \
        echo "✗ Failed to stop."
}

safia_restart() {
    systemctl --user restart safia.service safia-admin.service 2>/dev/null && \
        echo "✓ SAFIA restarted." || \
        echo "✗ Failed to restart."
}

safia_status() {
    systemctl --user status safia.service safia-admin.service 2>/dev/null || \
        echo "Service not found. Run 'safia start' first."
}

safia_logs() {
    local n="${1:-30}"
    local log_bot="$SAFIA_HOME/logs/bot.log"
    local log_admin="$SAFIA_HOME/logs/admin.log"
    if [ -f "$log_bot" ]; then
        echo "═══ Bot logs ($log_bot) ═══"
        tail -n "$n" "$log_bot"
        echo ""
    fi
    if [ -f "$log_admin" ]; then
        echo "═══ Admin logs ($log_admin) ═══"
        tail -n "$n" "$log_admin"
    elif [ ! -f "$log_bot" ]; then
        journalctl --user -u safia.service -u safia-admin.service -n "$n" --no-pager 2>/dev/null || \
            echo "No logs found."
    fi
}
DAEMON_LINUX
            ;;
        macos)
            cat << 'DAEMON_MACOS'
safia_start() {
    local agents_dir="$HOME/Library/LaunchAgents"
    local plist_bot="$agents_dir/com.safia.bot.plist"
    local plist_admin="$agents_dir/com.safia.admin.plist"

    if [ ! -f "$INSTALL_DIR/.env" ]; then
        echo "✗ No .env found. Run 'safia setup' first to configure."
        return 1
    fi

    if [ ! -f "$plist_bot" ] || [ ! -f "$plist_admin" ]; then
        mkdir -p "$agents_dir"
        mkdir -p "$SAFIA_HOME/logs"
    fi

    if [ ! -f "$plist_bot" ]; then
        cat > "$plist_bot" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.safia.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>__INSTALL_DIR__/.venv/bin/python</string>
        <string>main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>__INSTALL_DIR__</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>__SAFIA_HOME__/logs/bot.log</string>
    <key>StandardErrorPath</key>
    <string>__SAFIA_HOME__/logs/bot.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
PLIST
        sed -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" -e "s|__SAFIA_HOME__|$SAFIA_HOME|g" "$plist_bot" > "${plist_bot}.tmp" && mv "${plist_bot}.tmp" "$plist_bot"
    fi

    if [ ! -f "$plist_admin" ]; then
        cat > "$plist_admin" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.safia.admin</string>
    <key>ProgramArguments</key>
    <array>
        <string>__INSTALL_DIR__/.venv/bin/python</string>
        <string>admin_dashboard.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>__INSTALL_DIR__</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>__SAFIA_HOME__/logs/admin.log</string>
    <key>StandardErrorPath</key>
    <string>__SAFIA_HOME__/logs/admin.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
PLIST
        sed -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" -e "s|__SAFIA_HOME__|$SAFIA_HOME|g" "$plist_admin" > "${plist_admin}.tmp" && mv "${plist_admin}.tmp" "$plist_admin"
        echo "→ Daemon configured (auto-start on login enabled)."
    fi

    local started=true
    if ! launchctl list com.safia.bot &>/dev/null; then
        launchctl bootstrap "gui/$UID" "$plist_bot" 2>/dev/null || started=false
    fi
    if ! launchctl list com.safia.admin &>/dev/null; then
        launchctl bootstrap "gui/$UID" "$plist_admin" 2>/dev/null || started=false
    fi
    launchctl kickstart "gui/$UID/com.safia.bot" 2>/dev/null
    launchctl kickstart "gui/$UID/com.safia.admin" 2>/dev/null

    if [ "$started" = true ]; then
        echo "✓ SAFIA started (bot + admin dashboard on http://127.0.0.1:5454)."
    else
        echo "✗ Failed to start. Check logs: safia logs"
    fi
}

safia_stop() {
    local ok=true
    launchctl bootout "gui/$UID/com.safia.bot" 2>/dev/null || ok=false
    launchctl bootout "gui/$UID/com.safia.admin" 2>/dev/null || ok=false
    if [ "$ok" = true ]; then
        echo "✓ SAFIA stopped."
    else
        echo "SAFIA is not running."
    fi
}

safia_restart() {
    safia_stop
    sleep 1
    safia_start
}

safia_status() {
    local bot_running=false admin_running=false
    launchctl list com.safia.bot &>/dev/null && bot_running=true
    launchctl list com.safia.admin &>/dev/null && admin_running=true
    if [ "$bot_running" = true ] && [ "$admin_running" = true ]; then
        echo "✓ SAFIA is running (bot + admin dashboard on http://127.0.0.1:5454)"
    elif [ "$bot_running" = true ]; then
        echo "⚠ Bot is running but admin dashboard is not."
    elif [ "$admin_running" = true ]; then
        echo "⚠ Admin dashboard is running but bot is not."
    else
        echo "✗ SAFIA is not running."
    fi
}

safia_logs() {
    local n="${1:-30}"
    local log_bot="$SAFIA_HOME/logs/bot.log"
    local log_admin="$SAFIA_HOME/logs/admin.log"
    if [ -f "$log_bot" ]; then
        echo "═══ Bot logs ($log_bot) ═══"
        tail -n "$n" "$log_bot"
        echo ""
    fi
    if [ -f "$log_admin" ]; then
        echo "═══ Admin logs ($log_admin) ═══"
        tail -n "$n" "$log_admin"
    elif [ ! -f "$log_bot" ]; then
        echo "No logs found."
    fi
}
DAEMON_MACOS
            ;;
    esac
}

# ── Install safia command ───────────────────────────────────────────────────

install_safia_command() {
    local bin_dir
    bin_dir="$(get_bin_dir)"
    mkdir -p "$bin_dir"

    local wrapper="$bin_dir/safia"

    cat > "$wrapper" << 'WRAPPER_HEAD'
#!/usr/bin/env bash
# SAFIA CLI — unified command interface
set -e

SAFIA_HOME="${SAFIA_HOME:-$HOME/.safia}"
INSTALL_DIR="${SAFIA_INSTALL_DIR:-$SAFIA_HOME/safia}"

if [ ! -d "$INSTALL_DIR" ]; then
    echo "SAFIA is not installed. Run the installer first:"
    echo "  curl -fsSL https://raw.githubusercontent.com/superXdev/SAFIA/main/install.sh | bash"
    exit 1
fi

WRAPPER_HEAD

    generate_daemon_control_functions >> "$wrapper"

    cat >> "$wrapper" << 'WRAPPER_BODY'

cd "$INSTALL_DIR"

case "${1:-}" in
    setup)
        shift
        exec "$INSTALL_DIR/.venv/bin/python" scripts/setup.py "$@"
        ;;
    config)
        shift
        exec "$INSTALL_DIR/.venv/bin/python" scripts/config.py "$@"
        ;;
    access)
        shift
        exec "$INSTALL_DIR/.venv/bin/python" -m services.db_settings_cli "$@"
        ;;
    start)
        safia_start
        ;;
    stop)
        safia_stop
        ;;
    restart)
        safia_restart
        ;;
    status)
        safia_status
        ;;
    logs)
        safia_logs "${2:-30}"
        ;;
    test)
        exec "$INSTALL_DIR/.venv/bin/python" -m pytest tests/ -v "$@"
        ;;
    update)
        echo "→ Updating SAFIA..."
        git fetch origin main
        git checkout main
        git pull --ff-only origin main

        if [ -x "$SAFIA_HOME/bin/uv" ]; then
            _uv="$SAFIA_HOME/bin/uv"
        elif command -v uv >/dev/null 2>&1; then
            _uv="$(command -v uv)"
        elif [ -x "$INSTALL_DIR/.venv/bin/python" ]; then
            _uv="$INSTALL_DIR/.venv/bin/python -m uv"
        else
            echo "✗ uv not found. Install it: https://docs.astral.sh/uv/getting-started/installation/"
            exit 1
        fi
        $_uv sync
        safia_restart
        echo "✓ SAFIA updated and restarted."
        ;;
    uninstall)
        echo "This will permanently remove SAFIA from your system."
        echo "  • $SAFIA_HOME (all code, config, data, logs)"
        echo "  • $HOME/.local/bin/safia (CLI command)"
        echo ""
        printf "Type 'yes' to confirm: "
        IFS= read -r confirm
        if [ "$confirm" != "yes" ]; then
            echo "Uninstall cancelled."
            exit 0
        fi
        safia_stop 2>/dev/null || true
        if [ "$(uname -s)" = "Linux" ] && command -v systemctl >/dev/null 2>&1; then
            systemctl --user disable safia.service safia-admin.service 2>/dev/null || true
            rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/safia.service" "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/safia-admin.service"
            systemctl --user daemon-reload 2>/dev/null || true
        elif [ "$(uname -s)" = "Darwin" ]; then
            rm -f "$HOME/Library/LaunchAgents/com.safia.bot.plist" "$HOME/Library/LaunchAgents/com.safia.admin.plist"
        fi
        rm -f "$HOME/.local/bin/safia"
        rm -rf "$SAFIA_HOME"
        echo "✓ SAFIA has been uninstalled."
        ;;
    -h|--help|help)
        echo "SAFIA — Asisten Keuangan Pribadi berbasis AI"
        echo ""
        echo "Usage: safia <command>"
        echo ""
        echo "Commands:"
        echo "  setup      Re-run the interactive setup wizard (create/update .env)"
        echo "  config     View and edit configuration"
        echo "  access     Manage bot access control (allow/deny users)"
        echo "  start      Start the bot daemon (auto-starts on reboot)"
        echo "  stop       Stop the bot daemon"
        echo "  restart    Restart the bot daemon"
        echo "  status     Show daemon status"
        echo "  logs       Show recent logs (optional: safia logs <N>)"
        echo "  test       Run the test suite"
        echo "  update     Pull latest changes, update deps, and restart"
        echo "  uninstall  Remove SAFIA completely"
        echo "  help       Show this help"
        exit 0
        ;;
    *)
        echo "Usage: safia <command>"
        echo "Commands: setup | config | access | start | stop | restart | status | logs | test | update | uninstall | help"
        exit 1
        ;;
esac
WRAPPER_BODY

    chmod +x "$wrapper"
    log_success "Installed safia command to $wrapper"

    if [[ ":$PATH:" != *":$bin_dir:"* ]]; then
        echo ""
        log_warn "$bin_dir is not in your PATH."
        echo ""
        echo -e "  Add it to your shell config:"
        echo ""
        echo -e "    ${BOLD}echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc${NC}"
        echo -e "    ${BOLD}source ~/.bashrc${NC}"
        echo ""
        echo -e "  Or for zsh:"
        echo ""
        echo -e "    ${BOLD}echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc${NC}"
        echo -e "    ${BOLD}source ~/.zshrc${NC}"
        echo ""
    fi
}


# ============================================================================
# Main
# ============================================================================

print_banner

echo ""
echo -e "This script will install SAFIA to ${BOLD}$SAFIA_HOME${NC}"
echo -e "and add the ${BOLD}safia${NC} command to your terminal."
echo -e "After setup, the bot runs as a background daemon (auto-start on reboot)."
echo -e "All components run locally: embedding model (ONNX), vector DB (Qdrant on-disk), SQLite."
echo ""

detect_os
resolve_install_layout
check_git
install_uv
check_python
clone_repo
install_deps
install_safia_command

echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  SAFIA installed successfully!${NC}"
echo ""
echo -e "  Next steps:"
echo -e "    ${BOLD}1. safia setup${NC}    Configure .env (API keys, token, database)"
echo -e "    ${BOLD}2. safia start${NC}    Start the bot + admin dashboard as daemons"
echo ""
echo -e "  Runs locally — no cloud dependencies:"
echo -e "    ${GREEN}●${NC} Embedding model  → ONNX via fastembed (384d, multilingual)"
echo -e "    ${GREEN}●${NC} Vector storage   → Qdrant on-disk at data/qdrant/"
echo -e "    ${GREEN}●${NC} Database         → SQLite at data/safia.db"
echo -e "    ${GREEN}●${NC} Admin dashboard  → http://127.0.0.1:5454"
echo ""
echo -e "  Other commands:"
echo -e "    ${BOLD}safia config${NC}     Edit configuration"
echo -e "    ${BOLD}safia status${NC}     Show daemon status"
echo -e "    ${BOLD}safia logs${NC}       Show recent logs"
echo -e "    ${BOLD}safia restart${NC}    Restart the bot daemon"
echo -e "    ${BOLD}safia stop${NC}       Stop the bot daemon"
echo -e "    ${BOLD}safia update${NC}     Update and restart"
echo -e "    ${BOLD}safia test${NC}       Run tests"
echo -e "    ${BOLD}safia uninstall${NC}  Remove SAFIA completely"
echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""
