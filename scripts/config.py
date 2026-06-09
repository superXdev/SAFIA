#!/usr/bin/env python3
"""CLI configuration manager for SAFIA bot.

Usage:
    safia config
"""

import os
import re
import secrets
import shutil
import sys
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

console = Console()

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

ENV_PATH = ROOT / ".env"


def _section(title: str) -> None:
    console.print()
    console.print(
        Panel(Align.center(Text(title, style="bold white")), border_style="bright_blue", padding=(0, 2))
    )


def _success(msg: str) -> None:
    console.print(f"  [green]+[/green] {msg}")


def _info(msg: str) -> None:
    console.print(f"  [bright_blue]i[/bright_blue]  {msg}")


def _warn(msg: str) -> None:
    console.print(f"  [yellow]![/yellow]  {msg}")


def _input_password(prompt: str, default: str = "") -> str:
    val = questionary.password(prompt, default=default, style=QS_STYLE).unsafe_ask()
    if val is None:
        raise KeyboardInterrupt
    return val.strip()


def _input_text(prompt: str, default: str = "", required: bool = False) -> str:
    kwargs = {"default": default, "style": QS_STYLE}
    if required:
        kwargs["validate"] = lambda v: True if v.strip() else "Cannot be empty."
    val = questionary.text(prompt, **kwargs).unsafe_ask()
    if val is None:
        raise KeyboardInterrupt
    return val.strip() if val.strip() else default


# ── Env file reader/writer ─────────────────────────────────────────────────────

def load_env() -> dict[str, str]:
    """Parse .env into a dict, preserving comments as comment_ keys."""
    vals: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key, _, value = stripped.partition("=")
                vals[key.strip()] = value.strip()
    return vals


def save_env(vals: dict[str, str]) -> None:
    """Write dict back to .env, preserving comments and empty lines."""
    existing: list[str] = []
    if ENV_PATH.exists():
        existing = ENV_PATH.read_text(encoding="utf-8").splitlines()

    new_lines: list[str] = []
    seen: set[str] = set()
    for line in existing:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if "=" in stripped:
            key = stripped.partition("=")[0].strip()
            if key in vals:
                new_lines.append(f"{key}={vals[key]}")
                seen.add(key)
                continue
        new_lines.append(line)

    for key, value in vals.items():
        if key not in seen:
            new_lines.append(f"{key}={value}")

    backup = ENV_PATH.with_suffix(".backup")
    if ENV_PATH.exists():
        shutil.copy2(ENV_PATH, backup)
    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    _success("Configuration saved (.env.backup created)")


# ── Section editors ────────────────────────────────────────────────────────────

def edit_telegram(vals: dict) -> None:
    _section("Telegram Bot Token")
    _info("Get this from @BotFather on Telegram.")
    vals["TELEGRAM_BOT_TOKEN"] = _input_password("Token:", vals.get("TELEGRAM_BOT_TOKEN", ""))
    if not vals["TELEGRAM_BOT_TOKEN"]:
        del vals["TELEGRAM_BOT_TOKEN"]


def edit_provider(vals: dict) -> None:
    _section("AI Provider")
    current = vals.get("LLM_PROVIDER", "lunos")
    choice = questionary.select(
        "Choose provider:",
        choices=[
            questionary.Choice(f"Lunos — AI gateway Indonesia {'(current)' if current == 'lunos' else ''}", value="lunos"),
            questionary.Choice(f"Groq — Fast, free tier {'(current)' if current == 'groq' else ''}", value="groq"),
            questionary.Choice(f"OpenAI {'(current)' if current == 'openai' else ''}", value="openai"),
            questionary.Choice(f"Custom — own endpoint {'(current)' if current == 'custom' else ''}", value="custom"),
        ],
        style=QS_STYLE,
    ).unsafe_ask()
    if choice is None:
        raise KeyboardInterrupt
    vals["LLM_PROVIDER"] = choice

    if choice == "custom":
        base = _input_text("Base URL (OpenAI-compatible):", vals.get("LLM_BASE_URL", ""), required=True)
        vals["LLM_BASE_URL"] = base
    else:
        vals.pop("LLM_BASE_URL", None)

    key = _input_password(f"API Key for {choice}:", vals.get("LLM_API_KEY", ""))
    if key:
        vals["LLM_API_KEY"] = key


def edit_model(vals: dict) -> None:
    _section("AI Model")
    vals["LLM_MODEL"] = _input_text("Model ID:", vals.get("LLM_MODEL", ""), required=True)


def edit_groq_key(vals: dict) -> None:
    _section("Groq API Key (Whisper)")
    _info("Required for voice transcription. Uses Groq regardless of main provider.")
    key = _input_password("Groq API Key:", vals.get("GROQ_API_KEY", ""))
    if key:
        vals["GROQ_API_KEY"] = key
    else:
        vals.pop("GROQ_API_KEY", None)
        _info("Voice messages will be disabled.")


def edit_serpapi(vals: dict) -> None:
    _section("SerpAPI Key")
    _info("For financial news search. Sign up at serpapi.com")
    key = _input_password("SerpAPI Key:", vals.get("SERPAPI_KEY", ""))
    if key:
        vals["SERPAPI_KEY"] = key
    else:
        vals.pop("SERPAPI_KEY", None)
        _info("News search will be disabled.")


def edit_database(vals: dict) -> None:
    _section("Database")
    vals["DATABASE_URL"] = _input_text(
        "DATABASE_URL:", vals.get("DATABASE_URL", "sqlite+aiosqlite:///data/safia.db"), required=True
    )


def edit_redis(vals: dict) -> None:
    _section("Redis")
    vals["REDIS_URL"] = _input_text("REDIS_URL:", vals.get("REDIS_URL", "redis://localhost:6379/0"), required=True)


def edit_admin(vals: dict) -> None:
    _section("Admin Dashboard")
    enable = questionary.confirm("Enable admin dashboard?", default=True, style=QS_STYLE).unsafe_ask()
    if not enable:
        for k in ("ADMIN_USERNAME", "ADMIN_PASSWORD", "FLASK_SECRET_KEY"):
            vals.pop(k, None)
        return

    vals["ADMIN_USERNAME"] = _input_text("Username:", vals.get("ADMIN_USERNAME", "admin"), required=True)
    pw = _input_password("Password (blank = random):", vals.get("ADMIN_PASSWORD", ""))
    vals["ADMIN_PASSWORD"] = pw if pw else secrets.token_urlsafe(12)
    vals["FLASK_SECRET_KEY"] = vals.get("FLASK_SECRET_KEY", secrets.token_urlsafe(24))


def edit_advanced(vals: dict) -> None:
    """Edit less common settings."""
    _section("Advanced Settings")

    vals["LLM_MODEL"] = _input_text("LLM_MODEL:", vals.get("LLM_MODEL", "openai/gpt-oss-120b"))

    vision = _input_text("VISION_MODEL:", vals.get("VISION_MODEL", "mistralai/mistral-small-3.2-24b-instruct"))
    if vision:
        vals["VISION_MODEL"] = vision

    remind = questionary.confirm(
        "Enable reminders?", default=vals.get("REMINDER_ENABLED", "true") == "true", style=QS_STYLE
    ).unsafe_ask()
    vals["REMINDER_ENABLED"] = "true" if remind else "false"

    if remind:
        vals["REMINDER_MAX_PER_USER"] = _input_text(
            "Max reminders per user:", vals.get("REMINDER_MAX_PER_USER", "10")
        )
        vals["REMINDER_TICK_SECONDS"] = _input_text(
            "Check interval (seconds):", vals.get("REMINDER_TICK_SECONDS", "30")
        )

    rate = _input_text("Daily message limit:", vals.get("DAILY_MESSAGE_LIMIT", "25"))
    if rate:
        vals["DAILY_MESSAGE_LIMIT"] = rate


# ── View ───────────────────────────────────────────────────────────────────────

def show_config(vals: dict) -> None:
    _section("Current Configuration")

    table = Table(show_header=False, border_style="bright_blue", padding=(0, 1))
    table.add_column("Key", style="bold cyan")
    table.add_column("Value", style="white")

    display_order = [
        "TELEGRAM_BOT_TOKEN", "LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL",
        "LLM_BASE_URL", "GROQ_API_KEY", "SERPAPI_KEY",
        "DATABASE_URL", "REDIS_URL",
        "ADMIN_USERNAME", "ADMIN_PASSWORD", "FLASK_SECRET_KEY",
        "VISION_MODEL", "REMINDER_ENABLED", "REMINDER_MAX_PER_USER",
        "REMINDER_TICK_SECONDS", "DAILY_MESSAGE_LIMIT",
    ]

    for key in display_order:
        if key in vals:
            value = vals[key]
            if any(s in key.upper() for s in ("KEY", "TOKEN", "PASSWORD", "SECRET")):
                value = value[:8] + "..." if len(value) > 8 else value
            table.add_row(key, value)

    for key, value in vals.items():
        if key not in display_order:
            table.add_row(key, value)

    console.print(table)


# ── Main ──────────────────────────────────────────────────────────────────────

MENU_ITEMS = [
    ("View configuration", show_config),
    ("Telegram Bot Token", edit_telegram),
    ("AI Provider & API Key", edit_provider),
    ("AI Model", edit_model),
    ("Groq Key (voice transcription)", edit_groq_key),
    ("SerpAPI Key (news search)", edit_serpapi),
    ("Database URL", edit_database),
    ("Redis URL", edit_redis),
    ("Admin Dashboard", edit_admin),
    ("Advanced settings", edit_advanced),
]


def main() -> None:
    console.clear()
    console.print()
    console.print(
        Panel(
            Align.center(Text("SAFIA Configuration Manager", style="bold bright_cyan")),
            border_style="bright_cyan",
            padding=(1, 4),
        )
    )
    console.print()

    if not ENV_PATH.exists():
        _warn("No .env file found. Run setup first: safia setup")
        sys.exit(1)

    vals = load_env()

    while True:
        choices = [questionary.Choice(item[0], value=i) for i, item in enumerate(MENU_ITEMS)]
        choices.append(questionary.Separator())
        choices.append(questionary.Choice("Save & Exit", value=-1))
        choices.append(questionary.Choice("Exit without saving", value=-2))

        idx = questionary.select("What would you like to configure?", choices=choices, style=QS_STYLE).unsafe_ask()

        if idx is None or idx == -2:
            console.print("\n  [yellow]Exited without saving.[/yellow]")
            sys.exit(0)
        if idx == -1:
            break

        try:
            MENU_ITEMS[idx][1](vals)
        except KeyboardInterrupt:
            continue

    save_env(vals)
    console.print()
    console.print(
        Panel(
            Align.center(Text("Configuration saved! Restart the bot to apply changes.", style="bold green")),
            border_style="green",
            padding=(1, 4),
        )
    )
    console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n  [yellow]Cancelled.[/yellow]")
        sys.exit(0)
