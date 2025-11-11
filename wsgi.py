from app import create_app

# WSGI 入口（Gunicorn/Uwsgi 可用）
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))