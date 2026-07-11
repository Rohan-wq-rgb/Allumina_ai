import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if os.path.exists(os.path.join(BASE_DIR, ".env")):
    load_dotenv(os.path.join(BASE_DIR, ".env"))
elif os.path.exists(os.path.join(os.path.dirname(BASE_DIR), ".env")):
    load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url or f"sqlite:///{os.path.join(BASE_DIR, 'allumina.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
