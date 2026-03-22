"""Flask admin dashboard app factory."""
import os

from flask import Flask

from config import KB_MAX_UPLOAD_MB


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-change-me")
    app.config["MAX_CONTENT_LENGTH"] = max(1, KB_MAX_UPLOAD_MB) * 1024 * 1024

    from admin.routes import bp, init_admin_db

    app.register_blueprint(bp)
    init_admin_db()

    return app
