#!/usr/bin/env python3
"""Interactive SAFIA setup wizard — TUI edition.

Usage:
    uv run python scripts/setup.py
"""

import os
import re
import secrets
import shutil
import sys
from pathlib import Path

import questionary
import requests
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

console = Console()

SAFIA_ASCII = r"""
   ███████╗ █████╗ ███████╗██╗ █████╗  
   ██╔════╝██╔══██╗██╔════╝██║██╔══██╗ 
   ███████╗███████║█████╗  ██║███████║ 
   ╚════██║██╔══██║██╔══╝  ██║██╔══██║ 
   ███████║██║  ██║██║     ██║██║  ██║ 
   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ 
"""

# ── questionary style ─────────────────────────────────────────────────────────

QS_STYLE = questionary.Style([
    ("qmark", "fg:#00d7ff bold"),
    ("question", "bold"),
    ("answer", "fg:#00d7ff bold"),
    ("pointer", "fg:#00d7ff bold"),
    ("highlighted", "fg:#00d7ff bold"),
    ("selected", ""),
    ("separator", "fg:#555555"),
    ("instruction", "fg:#888888 italic"),
    ("text", ""),
    ("disabled", "fg:#555555 italic"),
])


def _section(title: str) -> None:
    console.print()
    console.print(
        Panel(
            Align.center(Text(title, style="bold white")),
            border_style="bright_blue",
            padding=(0, 2),
        )
    )


def _success(msg: str) -> None:
    console.print(f"  [green]✓[/green] {msg}")


def _info(msg: str) -> None:
    console.print(f"  [bright_blue]ℹ[/bright_blue]  {msg}")


def _warn(msg: str) -> None:
    console.print(f"  [yellow]![/yellow]  {msg}")


def _input_required(prompt: str, *, default: str = "", validate: str = r".+") -> str:
    while True:
        val = questionary.text(
            prompt,
            default=default,
            style=QS_STYLE,
            validate=lambda v: True if re.match(validate, v) else t("cannot_be_empty"),
        ).unsafe_ask()
        if val is None:
            raise KeyboardInterrupt
        if re.match(validate, val.strip()):
            return val.strip()
        console.print(f"    [red]{t('input_cannot_be_empty')}[/red]")


def _input_optional(prompt: str, *, default: str = "") -> str:
    val = questionary.text(prompt, default=default, style=QS_STYLE).unsafe_ask()
    if val is None:
        raise KeyboardInterrupt
    return val.strip()


def _input_password(prompt: str) -> str:
    """Password-style input (masked)."""
    val = questionary.password(prompt, style=QS_STYLE).unsafe_ask()
    if val is None:
        raise KeyboardInterrupt
    return val.strip()


def _input_required_password(prompt: str) -> str:
    while True:
        val = questionary.password(
            prompt,
            style=QS_STYLE,
            validate=lambda v: True if re.match(r".+", v) else t("cannot_be_empty"),
        ).unsafe_ask()
        if val is None:
            raise KeyboardInterrupt
        if re.match(r".+", val.strip()):
            return val.strip()
        console.print(f"    [red]{t('input_cannot_be_empty')}[/red]")


# ── Translations ─────────────────────────────────────────────────────────────

LANG = "id"

TR = {
    "en": {
        "section_telegram": "Telegram Bot",
        "section_ai_provider": "Choose AI Provider",
        "section_serpapi": "SerpAPI",
        "section_database": "Database",
        "section_admin": "Admin Dashboard",
        "section_save": "Save Configuration",
        "section_language": "Language",
        "botfather": "Create a bot with @BotFather, paste the token.",
        "whisper_same": "Whisper will use the same Groq API Key.",
        "whisper_groq": "Whisper uses Groq. Skip if not needed.",
        "skip_optional": "Skip if not needed.",
        "serpapi_desc": "For financial news search. Sign up at serpapi.com",
        "fetching_models": "Fetching model list...",
        "sqlite_default": "Default: SQLite (zero-config)",
        "env_backup": "Old .env copied to .env.backup",
        "redis_docker": "Docker: docker run -d -p 6379:6379 --name safia-redis redis:7-alpine",
        "redis_missing": "Redis not detected. Bot requires Redis.",
        "model_fetch_fail": "Failed to fetch models. Enter manually.",
        "provider_chosen": "Provider: {provider}",
        "models_found": "Found {count} models.",
        "admin_creds": "Username: {user}, Password: {pw}",
        "env_saved": ".env saved",
        "choose_provider": "Choose provider:",
        "telegram_token": "TELEGRAM_BOT_TOKEN:",
        "api_key_lunos": "API Key Lunos (sk-...):",
        "api_key_groq": "API Key Groq (gsk_...):",
        "api_key_openai": "API Key OpenAI (sk-...):",
        "api_key_custom": "API Key Custom:",
        "model_select": "Choose model (type to search):",
        "model_manual": "Model name:",
        "whisper_key": "Groq API Key for Whisper (optional):",
        "serpapi_key": "SerpAPI Key (optional):",
        "custom_base_url": "Custom Base URL (OpenAI-compatible):",
        "database_url": "DATABASE_URL:",
        "redis_url": "REDIS_URL:",
        "press_enter_redis": "Press Enter when Redis is ready...",
        "enable_admin": "Enable admin dashboard?",
        "admin_username": "Admin username:",
        "admin_password": "Admin password (blank = random):",
        "cannot_be_empty": "Cannot be empty. Try again.",
        "input_cannot_be_empty": "Input cannot be empty. Try again.",
        "setup_complete": "Setup Complete!",
        "run_bot": "uv run python main.py",
        "run_dev": "uv run python run_dev.py",
        "run_admin": "uv run python admin_dashboard.py",
        "bot_label": "Bot:",
        "dev_label": "Dev:",
        "admin_label": "Admin:",
        "python_required": "Python 3.12+ required. Current:",
        "uv_not_found": "uv not found. Install:",
        "cancelled": "Cancelled.",
        "choice_lunos": "Lunos — AI gateway Indonesia",
        "choice_groq": "Groq — Fast, free tier",
        "choice_openai": "OpenAI",
        "choice_custom": "Custom — own endpoint",
        "language_prompt": "Choose language / Pilih bahasa:",
        "env_header": "# SAFIA .env",
        "env_provider": "# AI Provider: {provider}",
        "env_database": "# Database",
        "env_admin": "# Admin Dashboard",
        "env_groq_disabled": "# GROQ_API_KEY=  (not set, voice disabled)",
        "env_serpapi_disabled": "# SERPAPI_KEY=  (not set, search disabled)",
        "uv_sync": "uv sync...",
        "fetching_models_status": "Fetching models...",
    },
    "id": {
        "section_telegram": "Telegram Bot",
        "section_ai_provider": "Pilih AI Provider",
        "section_serpapi": "SerpAPI",
        "section_database": "Database",
        "section_admin": "Admin Dashboard",
        "section_save": "Simpan Konfigurasi",
        "section_language": "Bahasa",
        "botfather": "Buat bot di @BotFather, tempel token-nya.",
        "whisper_same": "Whisper akan pakai API Key Groq yang sama.",
        "whisper_groq": "Whisper pakai Groq. Kosongkan jika tidak perlu.",
        "skip_optional": "Kosongkan jika tidak perlu.",
        "serpapi_desc": "Untuk pencarian berita keuangan. Daftar di serpapi.com",
        "fetching_models": "Mengambil daftar model...",
        "sqlite_default": "Default: SQLite (zero-config)",
        "env_backup": ".env lama dicopy ke .env.backup",
        "redis_docker": "Docker: docker run -d -p 6379:6379 --name safia-redis redis:7-alpine",
        "redis_missing": "Redis tidak terdeteksi. Bot wajib Redis.",
        "model_fetch_fail": "Gagal fetch model. Masukkan manual.",
        "provider_chosen": "Provider: {provider}",
        "models_found": "Ditemukan {count} model.",
        "admin_creds": "Username: {user}, Password: {pw}",
        "env_saved": ".env tersimpan",
        "choose_provider": "Pilih provider:",
        "telegram_token": "TELEGRAM_BOT_TOKEN:",
        "api_key_lunos": "API Key Lunos (sk-...):",
        "api_key_groq": "API Key Groq (gsk_...):",
        "api_key_openai": "API Key OpenAI (sk-...):",
        "api_key_custom": "API Key Custom:",
        "model_select": "Pilih model (ketik untuk mencari):",
        "model_manual": "Nama model:",
        "whisper_key": "Groq API Key untuk Whisper (opsional):",
        "serpapi_key": "SerpAPI Key (opsional):",
        "custom_base_url": "Base URL Custom (harus OpenAI-compatible):",
        "database_url": "DATABASE_URL:",
        "redis_url": "REDIS_URL:",
        "press_enter_redis": "Tekan Enter setelah Redis siap...",
        "enable_admin": "Aktifkan admin dashboard?",
        "admin_username": "Username admin:",
        "admin_password": "Password admin (kosongkan = random):",
        "cannot_be_empty": "Tidak boleh kosong. Coba lagi.",
        "input_cannot_be_empty": "Masukkan tidak boleh kosong. Coba lagi.",
        "setup_complete": "Setup Selesai!",
        "run_bot": "uv run python main.py",
        "run_dev": "uv run python run_dev.py",
        "run_admin": "uv run python admin_dashboard.py",
        "bot_label": "Bot:",
        "dev_label": "Dev:",
        "admin_label": "Admin:",
        "python_required": "Python 3.12+ diperlukan. Versi saat ini:",
        "uv_not_found": "uv tidak ditemukan. Install:",
        "cancelled": "Dibatalkan.",
        "choice_lunos": "Lunos — AI gateway Indonesia",
        "choice_groq": "Groq — Cepat, free tier",
        "choice_openai": "OpenAI",
        "choice_custom": "Custom — endpoint sendiri",
        "language_prompt": "Choose language / Pilih bahasa:",
        "env_header": "# SAFIA .env",
        "env_provider": "# AI Provider: {provider}",
        "env_database": "# Database",
        "env_admin": "# Admin Dashboard",
        "env_groq_disabled": "# GROQ_API_KEY=  (tidak diset, voice dinonaktifkan)",
        "env_serpapi_disabled": "# SERPAPI_KEY=  (tidak diset, pencarian dinonaktifkan)",
        "uv_sync": "uv sync...",
        "fetching_models_status": "Fetching models...",
    },
}


def t(key: str, **kwargs) -> str:
    return TR[LANG].get(key, key).format(**kwargs)


def choose_language() -> str:
    _section(t("section_language"))
    choice = questionary.select(
        t("language_prompt"),
        choices=[
            questionary.Choice("Bahasa Indonesia", value="id"),
            questionary.Choice("English", value="en"),
        ],
        style=QS_STYLE,
    ).unsafe_ask()
    if choice is None:
        raise KeyboardInterrupt
    return choice


# ── Prerequisites ─────────────────────────────────────────────────────────────


def check_python() -> None:
    v = sys.version_info
    if v < (3, 12):
        console.print(f"[red]{t('python_required')} {v.major}.{v.minor}[/red]")
        sys.exit(1)


def check_uv() -> None:
    if shutil.which("uv") is None:
        console.print(f"[red]{t('uv_not_found')} https://docs.astral.sh/uv/getting-started/installation/[/red]")
        sys.exit(1)


def check_redis() -> None:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    result = s.connect_ex(("localhost", 6379))
    s.close()
    if result != 0:
        _warn(t("redis_missing"))
        _info(t("redis_docker"))
        questionary.text(
            t("press_enter_redis"),
            style=QS_STYLE,
        ).unsafe_ask()


# ── Sections ──────────────────────────────────────────────────────────────────


def configure_telegram() -> str:
    _section(t("section_telegram"))
    _info(t("botfather"))
    return _input_required_password(t("telegram_token"))


def choose_provider() -> tuple[str, str]:
    _section(t("section_ai_provider"))
    choice = questionary.select(
        t("choose_provider"),
        choices=[
            questionary.Choice(t("choice_lunos"), value="lunos"),
            questionary.Choice(t("choice_groq"), value="groq"),
            questionary.Choice(t("choice_openai"), value="openai"),
            questionary.Choice(t("choice_custom"), value="custom"),
        ],
        style=QS_STYLE,
    ).unsafe_ask()

    if choice is None:
        raise KeyboardInterrupt

    hints = {
        "lunos": "https://api.lunosrouter.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "openai": "https://api.openai.com/v1",
        "custom": "",
    }
    _success(t("provider_chosen", provider=choice))
    return choice, hints[choice]


def get_api_key(provider: str) -> str:
    prompts = {
        "lunos": t("api_key_lunos"),
        "groq": t("api_key_groq"),
        "openai": t("api_key_openai"),
        "custom": t("api_key_custom"),
    }
    return _input_password(prompts.get(provider, "API Key:"))


def _fetch_models(base_url: str, api_key: str) -> list[str] | None:
    """Fetch available model IDs from the provider's /v1/models endpoint.
    Returns sorted list of model IDs, or None on failure."""
    url = f"{base_url.rstrip('/')}/models"
    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        models = sorted(m.get("id", "") for m in data.get("data", []) if m.get("id"))
        return models if models else None
    except Exception:
        return None


def get_model(provider: str, base_url: str, api_key: str) -> str:
    defaults = {
        "lunos": "openai/gpt-4o",
        "groq": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "openai": "gpt-4o",
        "custom": "",
    }
    default = defaults.get(provider, "")

    _info(t("fetching_models"))
    models = None
    if base_url and api_key:
        with console.status(f"[bold bright_blue]{t('fetching_models_status')}[/bold bright_blue]"):
            models = _fetch_models(base_url, api_key)

    if models:
        _success(t("models_found", count=len(models)))
        if default not in models:
            default = models[0] if models else default
        choice = questionary.autocomplete(
            t("model_select"),
            choices=models,
            default=default,
            style=QS_STYLE,
            match_middle=True,
        ).unsafe_ask()
        if choice is None:
            raise KeyboardInterrupt
        return choice

    _warn(t("model_fetch_fail"))
    val = questionary.text(
        t("model_manual"),
        default=default,
        style=QS_STYLE,
        validate=lambda v: True if v.strip() else t("cannot_be_empty"),
    ).unsafe_ask()
    if val is None:
        raise KeyboardInterrupt
    return val.strip() if val.strip() else default


def get_groq_whisper_key(provider: str, api_key: str) -> str:
    if provider == "groq":
        _info(t("whisper_same"))
        return api_key
    _info(t("whisper_groq"))
    return _input_password(t("whisper_key"))


def get_serpapi_key() -> str:
    _section(t("section_serpapi"))
    _info(t("serpapi_desc"))
    _info(t("skip_optional"))
    return _input_password(t("serpapi_key"))


def get_custom_base_url() -> str:
    return _input_required(t("custom_base_url"))


def configure_database() -> str:
    _section(t("section_database"))
    default = "sqlite+aiosqlite:///data/safia.db"
    _info(t("sqlite_default"))
    val = questionary.text(
        t("database_url"),
        default=default,
        style=QS_STYLE,
    ).unsafe_ask()
    if val is None:
        raise KeyboardInterrupt
    return val.strip() if val.strip() else default


def configure_redis() -> str:
    default = "redis://localhost:6379/0"
    val = questionary.text(
        t("redis_url"),
        default=default,
        style=QS_STYLE,
    ).unsafe_ask()
    if val is None:
        raise KeyboardInterrupt
    return val.strip() if val.strip() else default


def configure_admin() -> tuple[str, str, str]:
    _section(t("section_admin"))
    enable = questionary.confirm(
        t("enable_admin"),
        default=True,
        style=QS_STYLE,
    ).unsafe_ask()

    if not enable:
        return "", "", ""

    user = questionary.text(
        t("admin_username"),
        default="admin",
        style=QS_STYLE,
    ).unsafe_ask()
    if user is None:
        raise KeyboardInterrupt
    user = user.strip() or "admin"

    pw = questionary.password(
        t("admin_password"),
        default=secrets.token_urlsafe(12),
        style=QS_STYLE,
    ).unsafe_ask()
    if pw is None:
        raise KeyboardInterrupt
    pw = pw.strip() or secrets.token_urlsafe(12)

    secret = secrets.token_urlsafe(24)
    _success(t("admin_creds", user=user, pw=pw))
    return user, pw, secret


# ── Write .env ────────────────────────────────────────────────────────────────


def write_env(
    telegram_token: str,
    provider: str,
    api_key: str,
    model: str,
    groq_whisper_key: str,
    serpapi_key: str,
    custom_base_url: str,
    database_url: str,
    redis_url: str,
    admin_user: str,
    admin_pass: str,
    flask_secret: str,
) -> None:
    env_path = ROOT / ".env"
    exists = env_path.exists()
    if exists:
        backup = ROOT / ".env.backup"
        shutil.copy2(env_path, backup)
        _info(t("env_backup"))

    lines = [
        t("env_header"),
        f"TELEGRAM_BOT_TOKEN={telegram_token}",
        f"",
        t("env_provider", provider=provider),
        f"LLM_PROVIDER={provider}",
        f"LLM_API_KEY={api_key}",
        f"LLM_MODEL={model}",
    ]
    if provider == "custom" and custom_base_url:
        lines.append(f"LLM_BASE_URL={custom_base_url}")

    lines.append(f"")
    if groq_whisper_key:
        lines.append(f"GROQ_API_KEY={groq_whisper_key}")
    else:
        lines.append(t("env_groq_disabled"))

    if serpapi_key:
        lines.append(f"SERPAPI_KEY={serpapi_key}")
    else:
        lines.append(t("env_serpapi_disabled"))

    lines += [
        f"",
        t("env_database"),
        f"DATABASE_URL={database_url}",
        f"REDIS_URL={redis_url}",
        f"",
        t("env_admin"),
        f"ADMIN_USERNAME={admin_user}",
        f"ADMIN_PASSWORD={admin_pass}",
        f"FLASK_SECRET_KEY={flask_secret}",
        f"",
    ]

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _success(t("env_saved"))


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    global LANG
    console.clear()
    console.print()
    console.print(
        Panel(
            Align.center(
                Text(SAFIA_ASCII, style="bold bright_cyan"),
                vertical="middle",
            ),
            border_style="bright_cyan",
            padding=(1, 4),
        )
    )
    console.print()

    LANG = choose_language()

    check_python()
    check_uv()

    if not (ROOT / ".venv").exists():
        with console.status(f"[bold bright_blue]{t('uv_sync')}[/bold bright_blue]"):
            os.system("uv sync")

    check_redis()

    # Telegram Bot
    telegram_token = configure_telegram()

    # AI Provider
    provider, hint = choose_provider()
    api_key = get_api_key(provider)
    custom_base_url = ""
    if provider == "custom":
        custom_base_url = get_custom_base_url()

    # Resolve base URL for model fetching
    base_urls = {
        "lunos": "https://api.lunosrouter.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "openai": "https://api.openai.com/v1",
        "custom": custom_base_url,
    }
    model_base_url = base_urls[provider]

    model = get_model(provider, model_base_url, api_key)

    # Whisper
    groq_whisper_key = get_groq_whisper_key(provider, api_key)

    # SerpAPI
    serpapi_key = get_serpapi_key()

    # Database
    database_url = configure_database()
    redis_url = configure_redis()

    # Admin
    admin_user, admin_pass, flask_secret = configure_admin()

    # Write
    console.print()
    _section(t("section_save"))
    write_env(
        telegram_token,
        provider,
        api_key,
        model,
        groq_whisper_key,
        serpapi_key,
        custom_base_url,
        database_url,
        redis_url,
        admin_user,
        admin_pass,
        flask_secret,
    )

    console.print()
    console.print(
        Panel(
            Align.center(
                Text(t("setup_complete"), style="bold green")
                + Text("\n\n")
                + Text(t("bot_label"), style="dim")
                + Text(f"  {t('run_bot')}", style="bright_cyan")
                + Text("\n")
                + Text(t("dev_label"), style="dim")
                + Text(f"  {t('run_dev')}", style="bright_cyan")
                + Text("\n")
                + Text(t("admin_label"), style="dim")
                + Text(f"  {t('run_admin')}", style="bright_cyan"),
                vertical="middle",
            ),
            border_style="green",
            padding=(1, 4),
        )
    )
    console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print()
        console.print(f"  [yellow]{t('cancelled')}[/yellow]")
        sys.exit(0)
