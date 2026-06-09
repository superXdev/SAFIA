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
RUN_SETUP=true
BRANCH="main"
NON_INTERACTIVE=false

# ── Parse arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-venv)
            USE_VENV=false
            shift
            ;;
        --skip-setup)
            RUN_SETUP=false
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
            echo "  --skip-setup       Skip interactive setup wizard"
            echo "  --branch NAME      Git branch to install (default: main)"
            echo "  --dir PATH         Custom install directory (default: ~/.safia/safia)"
            echo "  --safia-home PATH  Data/config directory (default: ~/.safia)"
            echo "  --non-interactive  Skip prompts that require user input"
            echo "  -h, --help         Show this help"
            echo ""
            echo "After install, use the 'safia' command:"
            echo "  safia setup      Re-run setup wizard"
            echo "  safia config     Edit configuration"
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
            echo "Unknown option: $1"
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
    echo "│   Asisten Keuangan Pribadi berbasis AI — Telegram Bot    │"
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

    if [ "$NON_INTERACTIVE" = true ] || [ ! -t 0 ]; then
        case "$default" in
            [yY]|[yY][eE][sS]|1) return 0 ;;
            *) return 1 ;;
        esac
    fi

    printf "%s %s " "$question" "$prompt_suffix"
    IFS= read -r answer || answer=""
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

# ── Redis check (non-blocking) ──────────────────────────────────────────────

check_redis() {
    log_info "Checking Redis..."
    if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
        log_success "Redis is running"
        return 0
    fi

    log_warn "Redis is not running. SAFIA requires Redis for chat history and rate limiting."
    log_info "Start Redis before running the bot:"
    log_info "  docker run -d -p 6379:6379 --name safia-redis redis:7-alpine"
    log_info "Or install Redis via your package manager."
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

# ── Daemon setup ────────────────────────────────────────────────────────────

install_systemd_daemon() {
    local service_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
    mkdir -p "$service_dir"

    local service_file="$service_dir/safia.service"
    local venv_python="$INSTALL_DIR/.venv/bin/python"
    local log_dir="$SAFIA_HOME/logs"
    mkdir -p "$log_dir"

    log_info "Creating systemd user service..."

    cat > "$service_file" << SYSTEMD_EOF
[Unit]
Description=SAFIA Telegram Bot
After=network-online.target redis.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$venv_python main.py
Restart=always
RestartSec=15
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:$log_dir/bot.log
StandardError=append:$log_dir/bot.log

[Install]
WantedBy=default.target
SYSTEMD_EOF

    systemctl --user daemon-reload
    systemctl --user enable safia.service
    systemctl --user start safia.service

    log_success "systemd service installed and started (auto-start on boot enabled)"
}

install_launchd_daemon() {
    local agents_dir="$HOME/Library/LaunchAgents"
    mkdir -p "$agents_dir"

    local plist_file="$agents_dir/com.safia.bot.plist"
    local venv_python="$INSTALL_DIR/.venv/bin/python"
    local log_dir="$SAFIA_HOME/logs"
    mkdir -p "$log_dir"

    log_info "Creating launchd agent..."

    cat > "$plist_file" << LAUNCHD_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.safia.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>$venv_python</string>
        <string>main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$log_dir/bot.log</string>
    <key>StandardErrorPath</key>
    <string>$log_dir/bot.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
LAUNCHD_EOF

    launchctl bootout "gui/$UID/com.safia.bot" 2>/dev/null || true
    launchctl bootstrap "gui/$UID" "$plist_file"
    launchctl kickstart "gui/$UID/com.safia.bot"

    log_success "launchd agent installed and started (auto-start on login enabled)"
}

install_daemon() {
    if [ ! -f "$INSTALL_DIR/.env" ]; then
        log_warn "No .env found — skipping daemon setup. Run 'safia setup' first."
        return 0
    fi

    echo ""
    log_info "Setting up background daemon (auto-starts on reboot)..."

    case "$OS" in
        linux)
            if command -v systemctl >/dev/null 2>&1 && systemctl --user >/dev/null 2>&1; then
                install_systemd_daemon
            else
                log_warn "systemd user services not available. Cannot set up daemon."
                log_info "Run the bot manually: cd $INSTALL_DIR && uv run python main.py"
            fi
            ;;
        macos)
            if command -v launchctl >/dev/null 2>&1; then
                install_launchd_daemon
            else
                log_warn "launchd not available. Cannot set up daemon."
                log_info "Run the bot manually: cd $INSTALL_DIR && uv run python main.py"
            fi
            ;;
    esac
}

# ── Daemon control helpers (for CLI wrapper) ────────────────────────────────

generate_daemon_control_functions() {
    case "$OS" in
        linux)
            cat << 'DAEMON_LINUX'
safia_start() {
    systemctl --user start safia.service 2>/dev/null && \
        echo "✓ SAFIA bot started." || \
        echo "✗ Failed to start. Check: systemctl --user status safia"
}

safia_stop() {
    systemctl --user stop safia.service 2>/dev/null && \
        echo "✓ SAFIA bot stopped." || \
        echo "✗ Failed to stop."
}

safia_restart() {
    systemctl --user restart safia.service 2>/dev/null && \
        echo "✓ SAFIA bot restarted." || \
        echo "✗ Failed to restart."
}

safia_status() {
    systemctl --user status safia.service 2>/dev/null || \
        echo "Service not found. Run 'safia start' first."
}

safia_logs() {
    local n="${1:-30}"
    if [ -f "$SAFIA_HOME/logs/bot.log" ]; then
        tail -n "$n" "$SAFIA_HOME/logs/bot.log"
    else
        journalctl --user -u safia.service -n "$n" --no-pager 2>/dev/null || \
            echo "No logs found."
    fi
}
DAEMON_LINUX
            ;;
        macos)
            cat << 'DAEMON_MACOS'
safia_start() {
    if launchctl list com.safia.bot &>/dev/null; then
        echo "SAFIA is already running."
        return 0
    fi
    launchctl bootstrap "gui/$UID" "$HOME/Library/LaunchAgents/com.safia.bot.plist" 2>/dev/null && \
        launchctl kickstart "gui/$UID/com.safia.bot" && \
        echo "✓ SAFIA bot started." || \
        echo "✗ Failed to start."
}

safia_stop() {
    launchctl bootout "gui/$UID/com.safia.bot" 2>/dev/null && \
        echo "✓ SAFIA bot stopped." || \
        echo "SAFIA is not running."
}

safia_restart() {
    safia_stop
    sleep 1
    safia_start
}

safia_status() {
    if launchctl list com.safia.bot &>/dev/null; then
        echo "✓ SAFIA is running (PID $(launchctl list com.safia.bot 2>/dev/null | awk 'NR>1{print $1}'))"
    else
        echo "✗ SAFIA is not running."
    fi
}

safia_logs() {
    local n="${1:-30}"
    if [ -f "$SAFIA_HOME/logs/bot.log" ]; then
        tail -n "$n" "$SAFIA_HOME/logs/bot.log"
    else
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
        exec uv run python scripts/setup.py "$@"
        ;;
    config)
        shift
        exec uv run python scripts/config.py "$@"
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
        exec uv run pytest tests/ -v "$@"
        ;;
    update)
        echo "→ Updating SAFIA..."
        git fetch origin main
        git checkout main
        git pull --ff-only origin main
        uv sync
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
            systemctl --user disable safia.service 2>/dev/null || true
            rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/safia.service"
            systemctl --user daemon-reload 2>/dev/null || true
        elif [ "$(uname -s)" = "Darwin" ]; then
            rm -f "$HOME/Library/LaunchAgents/com.safia.bot.plist"
        fi
        rm -f "$HOME/.local/bin/safia"
        rm -rf "$SAFIA_HOME"
        echo "✓ SAFIA has been uninstalled."
        echo "  Redis/Docker containers (if any) were not touched."
        ;;
    -h|--help|help)
        echo "SAFIA — Asisten Keuangan Pribadi berbasis AI"
        echo ""
        echo "Usage: safia <command>"
        echo ""
        echo "Commands:"
        echo "  setup      Re-run the interactive setup wizard (create/update .env)"
        echo "  config     View and edit configuration"
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
        echo "Commands: setup | config | start | stop | restart | status | logs | test | update | uninstall | help"
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

# ── Run setup wizard ────────────────────────────────────────────────────────

run_setup_wizard() {
    if [ "$RUN_SETUP" = false ]; then
        log_info "Skipping setup wizard (--skip-setup)."
        log_info "You must create $INSTALL_DIR/.env manually before running the bot."
        return 0
    fi

    if [ -f "$INSTALL_DIR/.env" ]; then
        log_info "Existing .env found at $INSTALL_DIR/.env"
        if ! prompt_yes_no "Re-run setup wizard?" "no"; then
            log_info "Skipping setup. Use 'safia setup' or 'safia config' to change settings later."
            return 0
        fi
    fi

    echo ""
    log_info "Launching setup wizard..."
    cd "$INSTALL_DIR"
    "$UV_CMD" run python scripts/setup.py
}

# ============================================================================
# Main
# ============================================================================

print_banner

echo ""
echo -e "This script will install SAFIA to ${BOLD}$SAFIA_HOME${NC}"
echo -e "and add the ${BOLD}safia${NC} command to your terminal."
echo -e "After setup, the bot runs as a background daemon (auto-start on reboot)."
echo ""

detect_os
resolve_install_layout
check_git
install_uv
check_python
check_redis
clone_repo
install_deps
install_safia_command
run_setup_wizard
install_daemon

echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  SAFIA installed successfully!${NC}"
echo ""
echo -e "  Status:             ${BOLD}safia status${NC}"
echo -e "  View logs:          ${BOLD}safia logs${NC}"
echo -e "  Restart:            ${BOLD}safia restart${NC}"
echo -e "  Reconfigure:        ${BOLD}safia config${NC}"
echo -e "  Update:             ${BOLD}safia update${NC}"
echo -e "  Stop daemon:        ${BOLD}safia stop${NC}"
echo -e "  Uninstall:          ${BOLD}safia uninstall${NC}"
echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""
