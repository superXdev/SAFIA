"""CLI for bot access control — called via `safia access <action>`."""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv()

from services.db_settings import (
    add_allowed_user,
    get_access_mode,
    get_allowed_users,
    remove_allowed_user,
    set_access_mode,
)
from services.database import init_db


def _run(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def main():
    if len(sys.argv) < 2:
        _print_usage()
        return

    action = sys.argv[1]

    if action == "mode":
        if len(sys.argv) < 3 or sys.argv[2] not in ("all", "allowlist"):
            print("Usage: safia access mode <all|allowlist>")
            return
        mode = sys.argv[2]
        _run(set_access_mode(mode))
        print(f"Access mode set to '{mode}'.")

    elif action == "add":
        if len(sys.argv) < 3:
            print("Usage: safia access add <telegram_id>")
            return
        try:
            tid = int(sys.argv[2])
        except ValueError:
            print("Invalid Telegram ID.")
            return
        _run(add_allowed_user(tid))
        print(f"User {tid} added to allowlist.")

    elif action == "remove":
        if len(sys.argv) < 3:
            print("Usage: safia access remove <telegram_id>")
            return
        try:
            tid = int(sys.argv[2])
        except ValueError:
            print("Invalid Telegram ID.")
            return
        _run(remove_allowed_user(tid))
        print(f"User {tid} removed from allowlist.")

    elif action == "list":
        mode = _run(get_access_mode())
        allowed = _run(get_allowed_users())
        print(f"Access mode: {mode}")
        if allowed:
            print("Allowed users:")
            for uid in allowed:
                print(f"  {uid}")
        else:
            print("No users in allowlist.")

    elif action in ("-h", "--help", "help"):
        _print_usage()
    else:
        print(f"Unknown action: {action}")
        _print_usage()


def _print_usage():
    print("SAFIA access control")
    print()
    print("Usage: safia access <action> [args]")
    print()
    print("Actions:")
    print("  mode <all|allowlist>   Set who can use the bot")
    print("  add <telegram_id>      Allow a specific user")
    print("  remove <telegram_id>   Revoke access from a user")
    print("  list                   Show current access settings")


if __name__ == "__main__":
    main()
