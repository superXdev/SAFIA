# ============================================================================
# SAFIA Installer — Windows (PowerShell)
# ============================================================================
# Installs the SAFIA Telegram bot and sets up auto-start via Scheduled Task.
#
# Usage:
#   iex (irm https://raw.githubusercontent.com/superXdev/SAFIA/main/install.ps1)
#
# Or with options:
#   & ([scriptblock]::Create((irm ...))) -Branch develop -SkipSetup
# ============================================================================

param(
    [switch]$SkipSetup,
    [string]$Branch = "main",
    [string]$InstallDir = "",
    [string]$SafiaHome = "",
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# ── Help ────────────────────────────────────────────────────────────────────
if ($Help) {
    Write-Host "SAFIA Installer — Windows"
    Write-Host ""
    Write-Host "Usage: install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipSetup          Skip the setup wizard after install"
    Write-Host "  -Branch NAME        Git branch to install (default: main)"
    Write-Host "  -InstallDir PATH    Custom install directory (default: ~\.safia\safia)"
    Write-Host "  -SafiaHome PATH     Data/config directory (default: ~\.safia)"
    Write-Host "  -Help               Show this help"
    Write-Host ""
    Write-Host "After install, use the 'safia' command:"
    Write-Host "  safia setup      Re-run setup wizard"
    Write-Host "  safia config     Edit configuration"
    Write-Host "  safia access     Manage bot access control"
    Write-Host "  safia start      Start the bot daemon"
    Write-Host "  safia stop       Stop the bot daemon"
    Write-Host "  safia restart    Restart the bot daemon"
    Write-Host "  safia status     Show daemon status"
    Write-Host "  safia logs       Show recent logs"
    Write-Host "  safia test       Run tests"
    Write-Host "  safia update     Pull latest changes, update deps, and restart"
    Write-Host "  safia uninstall  Remove SAFIA completely"
    return
}

# ── Configuration ───────────────────────────────────────────────────────────
$REPO_URL = "https://github.com/superXdev/SAFIA.git"

if (-not $SafiaHome) {
    $SafiaHome = Join-Path $env:USERPROFILE ".safia"
}
if (-not $InstallDir) {
    $InstallDir = Join-Path $SafiaHome "safia"
}

$VENV_DIR = Join-Path $InstallDir ".venv"
$LOG_DIR = Join-Path $SafiaHome "logs"
$TASK_NAME = "SAFIA Bot"
$TASK_NAME_ADMIN = "SAFIA Admin Dashboard"
$SAFIA_BIN = Join-Path $SafiaHome "bin"
$WRAPPER_PATH = Join-Path $SAFIA_BIN "safia.ps1"

# ── Output helpers ──────────────────────────────────────────────────────────
function Write-Step { Write-Host "`n>>> $($args[0])" -ForegroundColor Cyan }
function Write-OK   { Write-Host "    OK: $($args[0])" -ForegroundColor Green }
function Write-Warn { Write-Host "    WARN: $($args[0])" -ForegroundColor Yellow }
function Write-Err  { Write-Host "    ERROR: $($args[0])" -ForegroundColor Red }

# ── Prerequisites ───────────────────────────────────────────────────────────
Write-Step "Checking prerequisites..."

# Git
try {
    $gitVersion = (git --version 2>$null)
    if ($gitVersion) { Write-OK "git: $gitVersion" }
} catch {
    Write-Err "Git not found. Install from https://git-scm.com/download/win"
    exit 1
}

# Python
try {
    $pyVersion = (python --version 2>$null)
    if ($pyVersion) { Write-OK "python: $pyVersion" }
} catch {
    Write-Err "Python not found. Install from https://python.org/downloads/"
    exit 1
}

# uv
try {
    $uvVersion = (uv --version 2>$null)
    if ($uvVersion) { Write-OK "uv: $uvVersion" }
} catch {
    Write-Step "Installing uv..."
    try {
        irm https://astral.sh/uv/install.ps1 | iex
        $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
        Write-OK "uv installed"
    } catch {
        Write-Err "Failed to install uv. Install manually: irm https://astral.sh/uv/install.ps1 | iex"
        exit 1
    }
}

# ── Clone repository ────────────────────────────────────────────────────────
Write-Step "Cloning SAFIA repository..."
if (Test-Path $InstallDir) {
    Write-OK "Directory exists: $InstallDir"
    try {
        Push-Location $InstallDir
        $currentBranch = (git rev-parse --abbrev-ref HEAD)
        if ($currentBranch -ne $Branch) {
            Write-Step "Switching to branch $Branch..."
            git fetch origin
            git checkout $Branch
            git pull origin $Branch
        } else {
            Write-Step "Pulling latest changes on $Branch..."
            git pull origin $Branch
        }
        Pop-Location
    } catch {
        Write-Warn "Could not update repository. Continuing with existing code."
        Pop-Location
    }
} else {
    New-Item -ItemType Directory -Force -Path (Split-Path $InstallDir -Parent) | Out-Null
    git clone --branch $Branch $REPO_URL $InstallDir
    Write-OK "Cloned to $InstallDir"
}

# ── Create directories ──────────────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $SAFIA_BIN | Out-Null

# ── Install dependencies ────────────────────────────────────────────────────
Write-Step "Installing Python dependencies..."
Push-Location $InstallDir
try {
    if (Test-Path $VENV_DIR) {
        Write-OK "Virtual environment exists"
    }
    uv sync
    Write-OK "Dependencies installed"
} catch {
    Write-Err "Failed to install dependencies"
    Pop-Location
    exit 1
}

# ── Create safia wrapper ────────────────────────────────────────────────────
Write-Step "Creating safia wrapper..."
$wrapper = @'
# SAFIA CLI wrapper – auto-generated by install.ps1
param(
    [string]$Command,
    [string[]]$Args
)

$SAFIA_HOME = if ($env:SAFIA_HOME) { $env:SAFIA_HOME } else { Join-Path $env:USERPROFILE ".safia" }
$INSTALL_DIR = Join-Path $SAFIA_HOME "safia"
$PYTHON = Join-Path $INSTALL_DIR ".venv\Scripts\python.exe"
$LOG_DIR = Join-Path $SAFIA_HOME "logs"
$TASK_NAME = "SAFIA Bot"
$TASK_NAME_ADMIN = "SAFIA Admin Dashboard"

function Write-Banner {
    Write-Host ""
    Write-Host "   ░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓████████▓▒░ ░▒▓█▓▒░ ░▒▓██████▓▒░" -ForegroundColor Cyan
    Write-Host "   ░▒▓█▓▒░░░░   ░▒▓█▓▒░░░░   ░▒▓█▓▒░░░░░░      ░▒▓█▓▒░ ░▒▓█▓▒░░░░  " -ForegroundColor Cyan
    Write-Host "   ░▒▓█▓▒░░░░   ░▒▓█▓▒░░░░   ░▒▓█▓▒░░░░░░      ░▒▓█▓▒░ ░▒▓█▓▒░░░░  " -ForegroundColor Cyan
    Write-Host "    ░▒▓██████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░      ░▒▓█▓▒░ ░▒▓██████▓▒░" -ForegroundColor Cyan
    Write-Host "          ░▒▓█▓▒░ ░▒▓█▓▒░░░░   ░▒▓█▓▒░░░░░░      ░▒▓█▓▒░ ░▒▓█▓▒░░░░  " -ForegroundColor Cyan
    Write-Host "          ░▒▓█▓▒░ ░▒▓█▓▒░░░░   ░▒▓█▓▒░░░░░░      ░▒▓█▓▒░ ░▒▓█▓▒░░░░  " -ForegroundColor Cyan
    Write-Host "   ░▒▓███████▓▒░ ░▒▓█▓▒░░░░   ░▒▓█▓▒░░░░░░      ░▒▓█▓▒░ ░▒▓██████▓▒░" -ForegroundColor Cyan
    Write-Host ""
}

if (-not (Test-Path $PYTHON)) {
    Write-Host "✗ Python virtual environment not found at $PYTHON" -ForegroundColor Red
    Write-Host "  Run the installer again or re-create the venv." -ForegroundColor Red
    exit 1
}

function Start-SafiaBot {
    $task = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
    if ($task -and $task.State -eq "Running") {
        Write-Host "Bot is already running." -ForegroundColor Yellow
        return
    }
    if ($task) {
        Start-ScheduledTask -TaskName $TASK_NAME
    } else {
        Write-Host "No scheduled task found. Run 'safia setup' first." -ForegroundColor Yellow
        return
    }
    Start-Sleep -Seconds 2
    $task = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
    if ($task -and $task.State -eq "Running") {
        Write-Host "Bot started." -ForegroundColor Green
    }
}

function Stop-SafiaBot {
    $task = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "No scheduled task found." -ForegroundColor Yellow
        return
    }
    Stop-ScheduledTask -TaskName $TASK_NAME
    Start-Sleep -Seconds 2
    $task = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
    if ($task.State -ne "Running") {
        Write-Host "Bot stopped." -ForegroundColor Green
    }
}

function Restart-SafiaBot {
    Stop-SafiaBot
    Start-Sleep -Seconds 2
    Start-SafiaBot
}

function Get-SafiaStatus {
    $task = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "Status: not installed (no scheduled task)" -ForegroundColor Yellow
        return
    }
    $state = $task.State
    $color = if ($state -eq "Running") { "Green" } else { "Yellow" }
    Write-Host "Status: $state" -ForegroundColor $color
    Write-Host "Task: $TASK_NAME"
    Write-Host "Directory: $INSTALL_DIR"
}

function Get-SafiaLogs {
    $n = if ($Args -and $Args[0] -match '^\d+$') { [int]$Args[0] } else { 20 }
    $logFile = Join-Path $LOG_DIR "bot.log"
    if (Test-Path $logFile) {
        Get-Content $logFile -Tail $n
    } else {
        Write-Host "No logs found at $logFile" -ForegroundColor Yellow
    }
}

function Update-Safia {
    Write-Host "Pulling latest changes..." -ForegroundColor Cyan
    Push-Location $INSTALL_DIR
    git pull --ff-only origin main
    Write-Host "Updating dependencies..." -ForegroundColor Cyan
    & uv sync
    Pop-Location
    Write-Host "Update complete. Restart with 'safia restart'." -ForegroundColor Green
}

function Uninstall-Safia {
    Write-Host "This will remove SAFIA completely." -ForegroundColor Yellow
    $confirm = Read-Host "Are you sure? (yes/no)"
    if ($confirm -ne "yes") { return }

    Stop-SafiaBot
    Unregister-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue -Confirm:$false
    Unregister-ScheduledTask -TaskName $TASK_NAME_ADMIN -ErrorAction SilentlyContinue -Confirm:$false

    Remove-Item -Recurse -Force $SAFIA_HOME -ErrorAction SilentlyContinue
    Write-Host "SAFIA uninstalled." -ForegroundColor Green
}

function Create-ScheduledTask {
    param([string]$Name, [string]$Script)

    $exists = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if ($exists) { return }

    $action = New-ScheduledTaskAction -Execute $PYTHON -Argument "`"$Script`""
    $trigger = New-ScheduledTaskTrigger -AtLogon
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1)

    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
}

# ── Dispatch ─────────────────────────────────────────────────────────────────
switch ($Command) {
    "setup" {
        & $PYTHON "$INSTALL_DIR\scripts\setup.py" @Args
        if (Test-Path "$INSTALL_DIR\.env") {
            Write-Host "Setting up auto-start scheduled task..." -ForegroundColor Cyan
            Create-ScheduledTask -Name $TASK_NAME -Script "$INSTALL_DIR\main.py"
            Create-ScheduledTask -Name $TASK_NAME_ADMIN -Script "$INSTALL_DIR\admin_dashboard.py"
            Write-Host "Auto-start configured." -ForegroundColor Green
        }
    }
    "config" {
        & $PYTHON "$INSTALL_DIR\scripts\config.py" @Args
    }
    "access" {
        & $PYTHON "$INSTALL_DIR\services\db_settings_cli.py" @Args
    }
    "start" {
        Create-ScheduledTask -Name $TASK_NAME -Script "$INSTALL_DIR\main.py"
        Start-SafiaBot
    }
    "stop" {
        Stop-SafiaBot
    }
    "restart" {
        Restart-SafiaBot
    }
    "status" {
        Get-SafiaStatus
    }
    "logs" {
        Get-SafiaLogs @Args
    }
    "test" {
        Push-Location $INSTALL_DIR
        & uv run pytest tests/ -v
        Pop-Location
    }
    "update" {
        Update-Safia
    }
    "uninstall" {
        Uninstall-Safia
    }
    "help" {
        Write-Banner
        Write-Host "Usage: safia <command>" -ForegroundColor White
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor White
        Write-Host "  setup      Re-run the interactive setup wizard" -ForegroundColor Gray
        Write-Host "  config     View and edit configuration" -ForegroundColor Gray
        Write-Host "  access     Manage bot access control" -ForegroundColor Gray
        Write-Host "  start      Start the bot daemon" -ForegroundColor Gray
        Write-Host "  stop       Stop the bot daemon" -ForegroundColor Gray
        Write-Host "  restart    Restart the bot daemon" -ForegroundColor Gray
        Write-Host "  status     Show daemon status" -ForegroundColor Gray
        Write-Host "  logs       Show recent logs (optional: safia logs <N>)" -ForegroundColor Gray
        Write-Host "  test       Run the test suite" -ForegroundColor Gray
        Write-Host "  update     Pull latest changes, update deps, and restart" -ForegroundColor Gray
        Write-Host "  uninstall  Remove SAFIA completely" -ForegroundColor Gray
        Write-Host "  help       Show this help" -ForegroundColor Gray
    }
    default {
        Write-Banner
        Write-Host "Usage: safia <command>" -ForegroundColor White
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor White
        Write-Host "  setup      Re-run the interactive setup wizard" -ForegroundColor Gray
        Write-Host "  config     View and edit configuration" -ForegroundColor Gray
        Write-Host "  access     Manage bot access control" -ForegroundColor Gray
        Write-Host "  start      Start the bot daemon" -ForegroundColor Gray
        Write-Host "  stop       Stop the bot daemon" -ForegroundColor Gray
        Write-Host "  restart    Restart the bot daemon" -ForegroundColor Gray
        Write-Host "  status     Show daemon status" -ForegroundColor Gray
        Write-Host "  logs       Show recent logs (optional: safia logs <N>)" -ForegroundColor Gray
        Write-Host "  test       Run the test suite" -ForegroundColor Gray
        Write-Host "  update     Pull latest changes, update deps, and restart" -ForegroundColor Gray
        Write-Host "  uninstall  Remove SAFIA completely" -ForegroundColor Gray
        Write-Host "  help       Show this help" -ForegroundColor Gray
    }
}
'@

$wrapper | Out-File -FilePath $WRAPPER_PATH -Encoding UTF8 -Force
Write-OK "Wrapper created at $WRAPPER_PATH"

# ── Create batch launcher ───────────────────────────────────────────────────
$batchPath = Join-Path $SAFIA_BIN "safia.cmd"
@"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "$WRAPPER_PATH" %*
"@ | Out-File -FilePath $batchPath -Encoding ASCII -Force
Write-OK "Batch launcher created at $batchPath"

# ── Create PowerShell profile alias ─────────────────────────────────────────
Write-Step "Configuring safia command..."
$profileDir = Split-Path $PROFILE -Parent
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
}

$profileEntry = @"

# SAFIA CLI
function safia {
    & "$WRAPPER_PATH" @args
}
"@

if (Test-Path $PROFILE) {
    $currentProfile = Get-Content $PROFILE -Raw
    if ($currentProfile -notmatch [regex]::Escape("# SAFIA CLI")) {
        Add-Content $PROFILE $profileEntry
        Write-OK "Added safia function to PowerShell profile"
    } else {
        Write-OK "safia function already in profile"
    }
} else {
    $profileEntry | Out-File -FilePath $PROFILE -Encoding UTF8 -Force
    Write-OK "Created PowerShell profile with safia function"
}

# ── Add to PATH ─────────────────────────────────────────────────────────────
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notmatch [regex]::Escape($SAFIA_BIN)) {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$SAFIA_BIN", "User")
    $env:PATH = "$env:PATH;$SAFIA_BIN"
    Write-OK "Added $SAFIA_BIN to user PATH"
}

Pop-Location

# ── Done ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  SAFIA installed successfully!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart your terminal, or run:" -ForegroundColor White
Write-Host "     . `$PROFILE" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Configure your bot:" -ForegroundColor White
Write-Host "     safia setup" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Start the bot:" -ForegroundColor White
Write-Host "     safia start" -ForegroundColor Cyan

if (-not $SkipSetup) {
    Write-Host ""
    $runSetup = Read-Host "Run setup wizard now? (Y/n)"
    if ($runSetup -eq "" -or $runSetup -eq "y" -or $runSetup -eq "Y") {
        & "$VENV_DIR\Scripts\python.exe" "$InstallDir\scripts\setup.py"
    }
}
