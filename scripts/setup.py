#!/usr/bin/env python3
"""Interactive SAFIA setup wizard.

Usage:
    uv run python scripts/setup.py
"""

import os
import re
import secrets
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

os.chdir(ROOT)

# ── Prerequisites ────────────────────────────────────────────────────────────


def check_python() -> None:
    v = sys.version_info
    if v < (3, 12):
        sys.exit("Python 3.12+ is required. Current: %s.%s" % (v.major, v.minor))


def check_uv() -> None:
    if shutil.which("uv") is None:
        sys.exit(
            "uv not found. Install from https://docs.astral.sh/uv/getting-started/installation/"
        )


def check_redis() -> None:
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(("localhost", 6379))
        s.close()
        if result == 0:
            return
    except Exception:
        pass
    print(
        "\n[!] Redis tidak terdeteksi di localhost:6379.\n"
        "    Bot tidak bisa berjalan tanpa Redis. Jalankan Redis dulu.\n"
        "    Docker: docker run -d -p 6379:6379 --name safia-redis redis:7-alpine\n"
    )
    input("Tekan Enter setelah Redis siap (atau Ctrl+C untuk keluar)... ")


def check_postgres() -> None:
    prompt_db = (
        "\n[!] SAFIA sekarang pakai SQLite (file-based), tidak perlu PostgreSQL.\n"
        "    Database akan otomatis dibuat di data/safia.db.\n"
        "    Kalau ingin tetap pakai PostgreSQL, set DATABASE_URL nanti.\n"
    )
    print(prompt_db)


def _input_required(prompt: str, *, validate: str = r".+") -> str:
    while True:
        val = input(prompt).strip()
        if re.match(validate, val):
            return val
        print("    Masukkan tidak boleh kosong. Coba lagi.")


def _input_optional(prompt: str, *, default: str = "") -> str:
    val = input(prompt).strip()
    return val if val else default


# ── AI Provider ──────────────────────────────────────────────────────────────


def choose_provider() -> tuple[str, str, str]:
    print("\n" + "=" * 56)
    print("  Pilih Penyedia AI (AI Provider)")
    print("=" * 56)
    print(
        "\n  1. Lunos (default)   — Gateway AI Indonesia, akses banyak model\n"
        "                           https://lunosrouter.com\n"
        "  2. Groq               — Inference cepat, gratis tier tersedia\n"
        "  3. OpenAI             — GPT-4o, GPT-4.1, dsb\n"
        "  4. Custom             — Endpoint OpenAI-compatible sendiri\n"
    )
    while True:
        choice = input("\nPilih [1/2/3/4, default=1]: ").strip() or "1"
        if choice == "1":
            provider = "lunos"
            hint = "https://api.lunosrouter.com/v1"
            break
        elif choice == "2":
            provider = "groq"
            hint = "https://api.groq.com/openai/v1"
            break
        elif choice == "3":
            provider = "openai"
            hint = "https://api.openai.com/v1"
            break
        elif choice == "4":
            provider = "custom"
            hint = ""
            break
        print("    Pilih 1-4.")
    return provider, hint


def get_api_key(provider: str) -> str:
    print()
    if provider == "lunos":
        return _input_required("API Key Lunos    (lsk_...): ")
    elif provider == "groq":
        return _input_required("API Key Groq     (gsk_...): ")
    elif provider == "openai":
        return _input_required("API Key OpenAI   (sk-...):  ")
    else:
        return _input_required("API Key Custom:             ")


def get_model(provider: str) -> str:
    defaults = {
        "lunos": "openai/gpt-4o",
        "groq": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "openai": "gpt-4o",
        "custom": "",
    }
    default = defaults.get(provider, "")
    prompt = f"Nama model [{default}]: "
    val = input(prompt).strip()
    return val if val else default


def get_groq_whisper_key() -> str:
    print(
        "\n  Whisper (transkripsi suara) selalu pakai Groq.\n"
        "  Kalau tidak diisi, fitur voice message akan dinonaktifkan."
    )
    key = input("Groq API Key  (gsk_..., untuk Whisper) [optional]: ").strip()
    return key


def get_custom_base_url() -> str:
    return _input_required("Base URL Custom (harus OpenAI-compatible): ")


# ── Database ─────────────────────────────────────────────────────────────────


def configure_database() -> str:
    print("\n" + "=" * 56)
    print("  Database")
    print("=" * 56)
    default = "sqlite+aiosqlite:///data/safia.db"
    print(f"  Default: SQLite (file-based, zero-config)")
    val = _input_optional(f"  DATABASE_URL [{default}]: ", default=default)
    return val


def configure_redis() -> str:
    default = "redis://localhost:6379/0"
    val = _input_optional(f"REDIS_URL [{default}]: ", default=default)
    return val


# ── Admin Dashboard ──────────────────────────────────────────────────────────


def configure_admin() -> tuple[str, str, str]:
    print("\n" + "=" * 56)
    print("  Admin Dashboard (opsional)")
    print("=" * 56)
    enable = _input_optional("Aktifkan admin dashboard? [Y/n]: ", default="Y").lower()
    if enable in ("n", "no"):
        return "", "", ""
    user = _input_optional("Username admin [admin]: ", default="admin")
    pw = _input_optional(
        "Password admin (kosongkan = random): ", default=secrets.token_urlsafe(12)
    )
    secret = secrets.token_urlsafe(24)
    print(f"   → Username: {user}, Password: {pw}")
    return user, pw, secret


# ── TeleBot ────────────────────────────────────────────────────────────────


def configure_telegram() -> str:
    print("\n" + "=" * 56)
    print("  Telegram Bot")
    print("=" * 56)
    print(
        "  Buat bot di @BotFather (https://t.me/BotFather),\n"
        "  lalu tempel token-nya di sini."
    )
    return _input_required("TELEGRAM_BOT_TOKEN: ")


# ── Write .env ───────────────────────────────────────────────────────────────


def write_env(
    telegram_token: str,
    provider: str,
    api_key: str,
    model: str,
    groq_whisper_key: str,
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
        print(f"\n  .env yang lama disalin ke .env.backup")

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
    print(f"\n  .env berhasil dibuat di {env_path}")


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    print()
    print("=" * 56)
    print("   🚀  SAFIA — Setup Wizard")
    print("=" * 56)
    print("   Setup interaktif untuk menjalankan SAFIA bot.")
    print("   Ctrl+C kapan saja untuk batal.\n")

    check_python()
    check_uv()

    # Install dependencies
    if not (ROOT / ".venv").exists():
        print("\n  Menjalankan uv sync...")
        os.system("uv sync")

    check_redis()
    check_postgres()

    # TeleBot
    telegram_token = configure_telegram()

    # AI Provider
    provider, hint = choose_provider()
    api_key = get_api_key(provider)
    model = get_model(provider)
    custom_base_url = ""
    if provider == "custom":
        custom_base_url = get_custom_base_url()

    groq_whisper_key = get_groq_whisper_key()

    # Database
    database_url = configure_database()
    redis_url = configure_redis()

    # Admin
    admin_user, admin_pass, flask_secret = configure_admin()

    # Write
    write_env(
        telegram_token,
        provider,
        api_key,
        model,
        groq_whisper_key,
        custom_base_url,
        database_url,
        redis_url,
        admin_user,
        admin_pass,
        flask_secret,
    )

    print()
    print("=" * 56)
    print("  ✅  Setup selesai!")
    print("=" * 56)
    print(
        "\n"
        "  Jalankan bot:\n"
        "    uv run python main.py\n"
        "\n"
        "  Dev mode (auto-reload):\n"
        "    uv run python run_dev.py\n"
        "\n"
        "  Admin dashboard:\n"
        "    uv run python admin_dashboard.py\n"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDibatalkan.")
        sys.exit(0)
