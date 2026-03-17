"""Flask admin dashboard app factory."""
from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    from admin.routes import bp
    app.register_blueprint(bp)

    return app
