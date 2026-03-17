"""Run the admin dashboard.

Usage:
    uv run python admin_dashboard.py
"""
from admin import create_app
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5454, debug=True)
