"""Run the admin dashboard.

Usage:
    python admin_dashboard.py
"""
from dotenv import load_dotenv

load_dotenv()

from admin import create_app

app = create_app()

if __name__ == "__main__":
    import os

    host = os.environ.get("ADMIN_DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("ADMIN_DASHBOARD_PORT", "5454"))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)
