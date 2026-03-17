"""Admin dashboard routes."""
from datetime import datetime
import asyncio

from flask import Blueprint, render_template

from services.database import get_all_users_with_stats, get_daily_metrics, get_overall_metrics

bp = Blueprint("admin", __name__)

# Single event loop for all async DB calls in this process
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)


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
