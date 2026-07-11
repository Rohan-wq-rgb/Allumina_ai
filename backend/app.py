import os
from flask import Flask, send_from_directory
from flask_cors import CORS

try:
    from .config import Config
    from .models import db
    from .auth_routes import auth_bp
    from .chat_routes import chat_bp
except ImportError:
    from config import Config
    from models import db
    from auth_routes import auth_bp
    from chat_routes import chat_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))


def create_app():
    app = Flask(__name__, static_folder=ROOT_DIR, static_url_path="")
    app.config.from_object(Config)

    app.config.update(
        SESSION_COOKIE_SAMESITE="None",
        SESSION_COOKIE_SECURE=True,
    )

    cors_origins = os.environ.get(
        "CORS_ORIGINS",
        "https://rohan-wq-rgb.github.io,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000"
    ).split(",")

    CORS(app, supports_credentials=True, origins=[o.strip() for o in cors_origins if o.strip()])

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chat_bp, url_prefix="/api")

    @app.route("/")
    def serve_start():
        return send_from_directory(ROOT_DIR, "start.html")

    @app.route("/<path:filename>")
    def serve_static(filename):
        return send_from_directory(ROOT_DIR, filename)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
