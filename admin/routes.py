"""Admin dashboard routes."""
import asyncio
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
    f = request.files.get("file")
    title = (request.form.get("title") or "").strip()
    if not f or not f.filename:
        flash("Pilih file terlebih dahulu.", "error")
        return redirect(url_for("admin.knowledge"))
    raw_name = f.filename
    safe = secure_filename(raw_name)
    if not safe:
        flash("Nama file tidak valid.", "error")
        return redirect(url_for("admin.knowledge"))
    suffix = Path(safe).suffix.lower()
    if suffix not in ALLOWED_KB_SUFFIXES:
        flash("Hanya PDF, TXT, atau DOCX yang didukung.", "error")
        return redirect(url_for("admin.knowledge"))
    data = f.read()
    if not data:
        flash("File kosong.", "error")
        return redirect(url_for("admin.knowledge"))
    mime = f.mimetype or ""
    ok, msg = _loop.run_until_complete(
        ingest_bytes(filename=safe, mime_type=mime, data=data, title=title)
    )
    flash(msg, "success" if ok else "error")
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
