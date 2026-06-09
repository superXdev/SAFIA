"""Admin dashboard routes."""
import asyncio
import os
import re
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.wrappers import Response
from werkzeug.utils import secure_filename

from config import ADMIN_PASSWORD, ADMIN_USERNAME
from services.database import (
    get_all_users_with_stats,
    get_daily_metrics,
    get_overall_metrics,
    init_db,
    kb_delete_row,
    kb_get_by_id,
    kb_list_documents,
)
from services.db_settings import (
    add_allowed_user,
    get_access_mode,
    get_allowed_users,
    remove_allowed_user,
    set_access_mode,
)
from services.knowledge.ingest import delete_kb_document, ingest_bytes

bp = Blueprint("admin", __name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
DOTENV_PATH = ROOT_DIR / ".env"

SENSITIVE_SUFFIXES = ("_KEY", "_TOKEN", "_PASSWORD", "_SECRET")

# Complete list of editable env vars, grouped for display.
# Entries: (key, default_value, description, section)
ALL_ENV_VARS: list[tuple[str, str, str, str]] = [
    # --- Bot ---
    ("TELEGRAM_BOT_TOKEN", "", "Telegram bot token from @BotFather", "Bot"),
    # --- AI & Voice ---
    ("LLM_PROVIDER", "lunos", "LLM provider: lunos / groq / openai / custom", "AI & Voice"),
    ("LLM_API_KEY", "", "API key for the chosen LLM provider", "AI & Voice"),
    ("LLM_MODEL", "openai/gpt-oss-120b", "Model ID for chat completions", "AI & Voice"),
    ("LLM_BASE_URL", "", "Custom base URL (only for custom provider)", "AI & Voice"),
    ("GROQ_API_KEY", "", "API key for Groq Whisper transcription", "AI & Voice"),
    ("VISION_MODEL", "mistralai/mistral-small-3.2-24b-instruct", "Model for photo/document vision", "AI & Voice"),
    # --- Search & Data ---
    ("FIRECRAWL_API_KEY", "", "Firecrawl API key for web search and article fetching", "Search & Data"),
    ("COINGECKO_API_KEY", "", "CoinGecko API key (optional, for higher limits)", "Search & Data"),
    ("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3", "CoinGecko endpoint", "Search & Data"),
    ("CURRENCY_RATE_URL", "https://api.frankfurter.app/latest", "Exchange rate source URL", "Search & Data"),
    # --- Storage ---
    ("DATABASE_URL", "sqlite+aiosqlite:///data/safia.db", "Database connection string", "Storage"),
    ("REDIS_URL", "redis://localhost:6379/0", "Redis connection string", "Storage"),
    # --- Vector & Embeddings ---
    ("QDRANT_PATH", "data/qdrant", "Local Qdrant storage directory", "Vector & Embeddings"),
    ("QDRANT_URL", "", "Remote Qdrant URL (leave blank for local)", "Vector & Embeddings"),
    ("QDRANT_API_KEY", "", "Qdrant API key (remote mode)", "Vector & Embeddings"),
    ("KB_COLLECTION_NAME", "safia_kb", "Qdrant collection name", "Vector & Embeddings"),
    ("EMBEDDING_LOCAL", "true", "Use local fastembed (true) or remote API (false)", "Vector & Embeddings"),
    ("EMBEDDING_LOCAL_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "Local embedding model ID", "Vector & Embeddings"),
    ("EMBEDDING_BASE_URL", "https://api.lunosrouter.com/v1", "Remote embedding API base URL", "Vector & Embeddings"),
    ("EMBEDDING_API_KEY", "", "Remote embedding API key", "Vector & Embeddings"),
    ("EMBEDDING_MODEL", "openai/text-embedding-3-small", "Remote embedding model ID", "Vector & Embeddings"),
    ("EMBEDDING_VECTOR_SIZE", "384", "Embedding vector dimensions", "Vector & Embeddings"),
    # --- Knowledge Base ---
    ("KB_CHUNK_WORDS", "450", "Words per chunk", "Knowledge Base"),
    ("KB_CHUNK_OVERLAP_WORDS", "70", "Word overlap between chunks", "Knowledge Base"),
    ("KB_UPLOAD_DIR", "data/kb_uploads", "Upload temp directory", "Knowledge Base"),
    ("KB_MAX_UPLOAD_MB", "200", "Max upload size (MB)", "Knowledge Base"),
    ("KB_EMBED_BATCH_SIZE", "32", "Batch size for embedding", "Knowledge Base"),
    # --- Reminders ---
    ("REMINDER_ENABLED", "true", "Enable recurring reminders", "Reminders"),
    ("REMINDER_MAX_PER_USER", "10", "Max reminders per user", "Reminders"),
    ("REMINDER_MAX_SENDS_PER_DAY", "15", "Max reminder sends per day", "Reminders"),
    ("REMINDER_TICK_SECONDS", "30", "How often to check for due reminders (seconds)", "Reminders"),
    # --- Admin ---
    ("ADMIN_USERNAME", "admin", "Dashboard username", "Admin"),
    ("ADMIN_PASSWORD", "", "Dashboard password (blank = no auth)", "Admin"),
    ("FLASK_SECRET_KEY", "", "Flask session secret key", "Admin"),
]


def _build_env_display() -> dict[str, dict]:
    """Return all editable env vars with their current values, grouped by section.
    Values come from .env if set, otherwise from the default."""
    dotenv = _read_dotenv()

    _select_vars: dict[str, list[str]] = {
        "LLM_PROVIDER": ["lunos", "groq", "openai", "custom"],
        "EMBEDDING_LOCAL": ["true", "false"],
        "REMINDER_ENABLED": ["true", "false"],
    }

    grouped: dict[str, list[dict]] = {}
    for key, default, desc, section in ALL_ENV_VARS:
        val = dotenv.get(key, default)
        masked_val = val
        if any(key.upper().endswith(s) for s in SENSITIVE_SUFFIXES) and val:
            masked_val = val[:8] + "..." if len(val) > 8 else "***"
        is_set = key in dotenv
        is_sensitive = any(key.upper().endswith(s) for s in SENSITIVE_SUFFIXES)

        if key in _select_vars:
            input_type = "select"
            options = _select_vars[key]
        elif is_sensitive:
            input_type = "password"
        else:
            input_type = "text"

        grouped.setdefault(section, []).append(
            {
                "key": key,
                "value": masked_val,
                "raw_value": val,
                "desc": desc,
                "is_set": is_set,
                "is_sensitive": is_sensitive,
                "input_type": input_type,
                "options": options if input_type == "select" else [],
            }
        )
    return grouped

# Single event loop for all async DB calls in this process
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)


def init_admin_db() -> None:
    """Run schema init on the same loop as route handlers (avoids cross-loop engine binding)."""
    _loop.run_until_complete(init_db())


ALLOWED_KB_SUFFIXES = {".pdf", ".txt", ".docx"}


@bp.before_request
def _require_basic_auth() -> Response | None:
    if not ADMIN_PASSWORD:
        return None
    auth = request.authorization
    expected_user = ADMIN_USERNAME or "admin"
    if (
        auth
        and auth.username == expected_user
        and auth.password == ADMIN_PASSWORD
    ):
        return None
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="SAFIA Admin"'},
    )


@bp.route("/")
def dashboard() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    metrics = _loop.run_until_complete(get_overall_metrics())
    daily = _loop.run_until_complete(get_daily_metrics(30))

    labels = [row["date"] for row in daily]
    registrations = [row["registrations"] for row in daily]
    active_users = [row["active_users"] for row in daily]
    tokens = [row["total_tokens"] for row in daily]

    return render_template(
        "dashboard.html",
        title="SAFIA · Admin analytics",
        active="dashboard",
        env_label="local",
        now=now,
        metrics=metrics,
        daily_labels=labels,
        daily_registrations=registrations,
        daily_active_users=active_users,
        daily_tokens=tokens,
    )


@bp.route("/users")
def users() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = _loop.run_until_complete(get_all_users_with_stats())
    return render_template(
        "users.html",
        title="SAFIA · Users",
        active="users",
        env_label="local",
        now=now,
        rows=rows,
    )


@bp.route("/settings")
def settings() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = _loop.run_until_complete(get_access_mode())
    allowed = _loop.run_until_complete(get_allowed_users())
    env_vars = os.environ.copy()
    env_groups = _build_env_display()
    return render_template(
        "settings.html",
        title="SAFIA · Settings",
        active="settings",
        env_label="local",
        now=now,
        access_mode=mode,
        allowed_users=allowed,
        env_groups=env_groups,
        auth_enabled=bool(ADMIN_PASSWORD),
    )


@bp.route("/settings/access", methods=["POST"])
def settings_access():
    action = request.form.get("action", "")
    if action == "mode":
        mode = request.form.get("mode", "all")
        _loop.run_until_complete(set_access_mode(mode))
        flash(f"Access mode set to '{mode}'.", "success")
    elif action == "add":
        try:
            tid = int(request.form.get("telegram_id", "0"))
        except ValueError:
            flash("Invalid Telegram ID.", "error")
            return redirect(url_for("admin.settings"))
        _loop.run_until_complete(add_allowed_user(tid))
        flash(f"User {tid} added to allowlist.", "success")
    elif action == "remove":
        try:
            tid = int(request.form.get("telegram_id", "0"))
        except ValueError:
            flash("Invalid Telegram ID.", "error")
            return redirect(url_for("admin.settings"))
        _loop.run_until_complete(remove_allowed_user(tid))
        flash(f"User {tid} removed from allowlist.", "success")
    return redirect(url_for("admin.settings"))


@bp.route("/settings/env", methods=["POST"])
def settings_env():
    key = request.form.get("key", "").strip()
    value = request.form.get("value", "")
    if not key:
        flash("No variable key provided.", "error")
        return redirect(url_for("admin.settings"))

    is_sensitive = any(key.upper().endswith(s) for s in SENSITIVE_SUFFIXES)
    if is_sensitive and (value.endswith("...") or value in ("", "***")):
        flash(f"{key}: unchanged (value not modified).", "success")
        return redirect(url_for("admin.settings"))

    if not DOTENV_PATH.exists():
        flash("No .env file found.", "error")
        return redirect(url_for("admin.settings"))

    try:
        _write_dotenv_key(key, value)
        flash(f"{key} updated. Restart the bot for changes to take effect.", "success")
    except Exception:
        flash(f"Failed to update {key}.", "error")

    return redirect(url_for("admin.settings"))


def _read_dotenv() -> dict[str, str]:
    """Parse .env file into a dict (keys only, no values). Not used for reading — for display we use os.environ."""
    if not DOTENV_PATH.exists():
        return {}
    result: dict[str, str] = {}
    with open(DOTENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)', line)
            if m:
                val = m.group(2).strip()
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                result[m.group(1)] = val
    return result


def _write_dotenv_key(key: str, value: str) -> None:
    """Set or update a key in .env, preserving comments, blank lines, and all other keys.
    Uncomments commented-out keys (e.g. '# FIRECRAWL_API_KEY=') when setting a value."""
    lines_out: list[str] = []
    found = False
    key_upper = key.upper()

    val_out = value
    if " " in val_out or "#" in val_out or '"' in val_out:
        val_out = f'"{val_out}"'

    with open(DOTENV_PATH, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            # Handle commented-out key: # KEY=...
            if stripped.startswith("#") and not found:
                inner = stripped[1:].strip()
                m = re.match(r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)', inner)
                if m and m.group(1).upper() == key_upper:
                    lines_out.append(f"{m.group(1)}={val_out}")
                    found = True
                    continue

            if not stripped or stripped.startswith("#"):
                lines_out.append(line.rstrip("\n"))
                continue

            m = re.match(r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)', stripped)
            if m and m.group(1).upper() == key_upper:
                lines_out.append(f"{m.group(1)}={val_out}")
                found = True
            else:
                lines_out.append(line.rstrip("\n"))

    if not found:
        lines_out.append(f"{key_upper}={val_out}")

    with open(DOTENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out) + "\n")


@bp.route("/knowledge")
def knowledge() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = _loop.run_until_complete(kb_list_documents())
    return render_template(
        "knowledge.html",
        title="SAFIA · Knowledge base",
        active="knowledge",
        env_label="local",
        now=now,
        rows=rows,
        auth_enabled=bool(ADMIN_PASSWORD),
    )


@bp.route("/knowledge/upload", methods=["POST"])
def knowledge_upload():
    files = request.files.getlist("files")
    if not files:
        single = request.files.get("file")
        if single:
            files = [single]

    title = (request.form.get("title") or "").strip()
    if not files:
        flash("Pilih file terlebih dahulu.", "error")
        return redirect(url_for("admin.knowledge"))

    success_count = 0
    fail_count = 0

    for f in files:
        if not f or not f.filename:
            fail_count += 1
            flash("Ada file tanpa nama, dilewati.", "error")
            continue

        raw_name = f.filename
        safe = secure_filename(raw_name)
        if not safe:
            fail_count += 1
            flash(f"Nama file tidak valid: {raw_name}", "error")
            continue

        suffix = Path(safe).suffix.lower()
        if suffix not in ALLOWED_KB_SUFFIXES:
            fail_count += 1
            flash(f"{safe}: format tidak didukung (hanya PDF, TXT, DOCX).", "error")
            continue

        data = f.read()
        if not data:
            fail_count += 1
            flash(f"{safe}: file kosong.", "error")
            continue

        mime = f.mimetype or ""
        per_file_title = title if len(files) == 1 else ""
        ok, msg = _loop.run_until_complete(
            ingest_bytes(filename=safe, mime_type=mime, data=data, title=per_file_title)
        )
        if ok:
            success_count += 1
        else:
            fail_count += 1
        flash(f"{safe}: {msg}", "success" if ok else "error")

    if success_count and fail_count:
        flash(
            f"Upload selesai: {success_count} berhasil, {fail_count} gagal.",
            "success",
        )
    elif success_count:
        flash(f"Upload selesai: {success_count} file berhasil diindeks.", "success")
    else:
        flash("Upload gagal. Tidak ada file yang berhasil diindeks.", "error")

    return redirect(url_for("admin.knowledge"))


@bp.route("/knowledge/delete/<int:row_id>", methods=["POST"])
def knowledge_delete(row_id: int):
    row = _loop.run_until_complete(kb_get_by_id(row_id))
    if row is None:
        flash("Dokumen tidak ditemukan.", "error")
        return redirect(url_for("admin.knowledge"))
    doc_id = row.document_id
    _loop.run_until_complete(delete_kb_document(doc_id))
    _loop.run_until_complete(kb_delete_row(row_id))
    flash("Dokumen dihapus dari basis pengetahuan.", "success")
    return redirect(url_for("admin.knowledge"))
