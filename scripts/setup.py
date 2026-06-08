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
            validate=lambda v: True if re.match(validate, v) else "Tidak boleh kosong. Coba lagi.",
        ).unsafe_ask()
        if val is None:
            raise KeyboardInterrupt
        if re.match(validate, val.strip()):
            return val.strip()
        console.print("    [red]Masukkan tidak boleh kosong. Coba lagi.[/red]")


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


# ── Prerequisites ─────────────────────────────────────────────────────────────


def check_python() -> None:
    v = sys.version_info
    if v < (3, 12):
        console.print("[red]Python 3.12+ diperlukan. Versi saat ini: %s.%s[/red]" % (v.major, v.minor))
        sys.exit(1)


def check_uv() -> None:
    if shutil.which("uv") is None:
        console.print(
            "[red]uv tidak ditemukan. "
            "Install dari https://docs.astral.sh/uv/getting-started/installation/[/red]"
        )
        sys.exit(1)


def check_redis() -> None:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    result = s.connect_ex(("localhost", 6379))
    s.close()
    if result != 0:
        _warn("Redis tidak terdeteksi di localhost:6379.")
        _info("Bot tidak bisa berjalan tanpa Redis. Jalankan Redis dulu.")
        _info("Docker: docker run -d -p 6379:6379 --name safia-redis redis:7-alpine")
        questionary.text(
            "Tekan Enter setelah Redis siap (atau Esc untuk keluar)...",
            style=QS_STYLE,
        ).unsafe_ask()


# ── Sections ──────────────────────────────────────────────────────────────────


def configure_telegram() -> str:
    _section("Telegram Bot")
    _info("Buat bot di @BotFather (https://t.me/BotFather), lalu tempel token-nya di sini.")
    return _input_required("TELEGRAM_BOT_TOKEN:")


def choose_provider() -> tuple[str, str]:
    _section("Pilih Penyedia AI (AI Provider)")
    choice = questionary.select(
        "Pilih provider:",
        choices=[
            questionary.Choice(
                "Lunos (default) — Gateway AI Indonesia, akses banyak model",
                value="lunos",
            ),
            questionary.Choice(
                "Groq — Inference cepat, gratis tier tersedia",
                value="groq",
            ),
            questionary.Choice(
                "OpenAI — GPT-4o, GPT-4.1, dsb",
                value="openai",
            ),
            questionary.Choice(
                "Custom — Endpoint OpenAI-compatible sendiri",
                value="custom",
            ),
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
    _success(f"Provider: {choice}")
    return choice, hints[choice]


def get_api_key(provider: str) -> str:
    prompts = {
        "lunos": "API Key Lunos (lsk_...):",
        "groq": "API Key Groq (gsk_...):",
        "openai": "API Key OpenAI (sk-...):",
        "custom": "API Key Custom:",
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

    _info("Mengambil daftar model dari provider...")
    models = None
    if base_url and api_key:
        with console.status("[bold bright_blue]Fetching models...[/bold bright_blue]"):
            models = _fetch_models(base_url, api_key)

    if models:
        _success(f"Ditemukan {len(models)} model.")
        if default not in models:
            default = models[0] if models else default
        choice = questionary.autocomplete(
            "Pilih model (ketik untuk mencari):",
            choices=models,
            default=default,
            style=QS_STYLE,
            match_middle=True,
        ).unsafe_ask()
        if choice is None:
            raise KeyboardInterrupt
        return choice

    _warn("Gagal mengambil daftar model. Masukkan nama model manual.")
    val = questionary.text(
        "Nama model:",
        default=default,
        style=QS_STYLE,
        validate=lambda v: True if v.strip() else "Tidak boleh kosong.",
    ).unsafe_ask()
    if val is None:
        raise KeyboardInterrupt
    return val.strip() if val.strip() else default


def get_groq_whisper_key(provider: str, api_key: str) -> str:
    if provider == "groq":
        _info("Whisper akan menggunakan API Key Groq yang sama dengan provider utama.")
        return api_key
    _info("Whisper (transkripsi suara) selalu pakai Groq.")
    _info("Kalau tidak diisi, fitur voice message akan dinonaktifkan.")
    return _input_password("Groq API Key untuk Whisper (opsional):")


def get_serpapi_key() -> str:
    _section("SerpAPI — Pencarian Berita")
    _info("SerpAPI digunakan untuk mencari berita keuangan via Google Search.")
    _info("Daftar gratis di https://serpapi.com — dapatkan API key dari dashboard.")
    _info("Kalau tidak diisi, fitur pencarian berita akan dinonaktifkan.")
    return _input_password("SerpAPI Key (opsional):")


def get_custom_base_url() -> str:
    return _input_required("Base URL Custom (harus OpenAI-compatible):")


def configure_database() -> str:
    _section("Database")
    default = "sqlite+aiosqlite:///data/safia.db"
    _info(f"Default: SQLite (file-based, zero-config)")
    val = questionary.text(
        f"DATABASE_URL:",
        default=default,
        style=QS_STYLE,
    ).unsafe_ask()
    if val is None:
        raise KeyboardInterrupt
    return val.strip() if val.strip() else default


def configure_redis() -> str:
    default = "redis://localhost:6379/0"
    val = questionary.text(
        f"REDIS_URL:",
        default=default,
        style=QS_STYLE,
    ).unsafe_ask()
    if val is None:
        raise KeyboardInterrupt
    return val.strip() if val.strip() else default


def configure_admin() -> tuple[str, str, str]:
    _section("Admin Dashboard (opsional)")
    enable = questionary.confirm(
        "Aktifkan admin dashboard?",
        default=True,
        style=QS_STYLE,
    ).unsafe_ask()

    if not enable:
        return "", "", ""

    user = questionary.text(
        "Username admin:",
        default="admin",
        style=QS_STYLE,
    ).unsafe_ask()
    if user is None:
        raise KeyboardInterrupt
    user = user.strip() or "admin"

    pw = questionary.password(
        "Password admin (kosongkan = random):",
        default=secrets.token_urlsafe(12),
        style=QS_STYLE,
    ).unsafe_ask()
    if pw is None:
        raise KeyboardInterrupt
    pw = pw.strip() or secrets.token_urlsafe(12)

    secret = secrets.token_urlsafe(24)
    _success(f"Username: {user}, Password: {pw}")
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
        _info(".env yang lama disalin ke .env.backup")

    lines = [
        f"# SAFIA environment — generated by setup.py",
        f"TELEGRAM_BOT_TOKEN={telegram_token}",
        f"",
        f"# AI Provider: {provider}",
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
        lines.append(f"# GROQ_API_KEY=  (tidak diset — voice message dinonaktifkan)")

    if serpapi_key:
        lines.append(f"SERPAPI_KEY={serpapi_key}")
    else:
        lines.append(f"# SERPAPI_KEY=  (tidak diset — pencarian berita dinonaktifkan)")

    lines += [
        f"",
        f"# Database",
        f"DATABASE_URL={database_url}",
        f"REDIS_URL={redis_url}",
        f"",
        f"# Admin Dashboard",
        f"ADMIN_USERNAME={admin_user}",
        f"ADMIN_PASSWORD={admin_pass}",
        f"FLASK_SECRET_KEY={flask_secret}",
        f"",
    ]

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _success(f".env berhasil dibuat di {env_path}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
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

    check_python()
    check_uv()

    if not (ROOT / ".venv").exists():
        with console.status("[bold bright_blue]Menjalankan uv sync...[/bold bright_blue]"):
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
    _section("Menyimpan Konfigurasi")
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
                Text("Setup Selesai!", style="bold green")
                + Text("\n\n")
                + Text("Jalankan bot:", style="dim")
                + Text("\n  uv run python main.py", style="bright_cyan")
                + Text("\n\n")
                + Text("Dev mode (auto-reload):", style="dim")
                + Text("\n  uv run python run_dev.py", style="bright_cyan")
                + Text("\n\n")
                + Text("Admin dashboard:", style="dim")
                + Text("\n  uv run python admin_dashboard.py", style="bright_cyan"),
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
        console.print("  [yellow]Dibatalkan.[/yellow]")
        sys.exit(0)
