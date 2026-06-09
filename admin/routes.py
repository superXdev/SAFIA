"""Admin dashboard routes."""
import asyncio
import os
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
    env_vars = {k: v for k, v in sorted(os.environ.items()) if k.startswith(("LLM_", "TELEGRAM_", "DATABASE_", "REDIS_", "EMBEDDING_", "QDRANT_", "GROQ_", "ADMIN_", "REMINDER_", "KB_", "SERPAPI_", "COINGECKO_"))}
    masked_vars = {}
    for k, v in env_vars.items():
        if any(x in k.upper() for x in ("KEY", "TOKEN", "PASSWORD", "SECRET")):
            masked_vars[k] = v[:8] + "..." if len(v) > 8 else "***"
        else:
            masked_vars[k] = v
    return render_template(
        "settings.html",
        title="SAFIA · Settings",
        active="settings",
        env_label="local",
        now=now,
        access_mode=mode,
        allowed_users=allowed,
        env_vars=masked_vars,
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
