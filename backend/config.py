import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "à_remplacer")
    SQLITE_DB_PATH = BASE_DIR / "data" / "app.db"
    SQLITE_DB_PATH_STR = str(SQLITE_DB_PATH)
    HISTORY_PIN = os.getenv("HISTORY_PIN", "1234")
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SYSTEM_EMAIL_RECIPIENT = os.getenv("SYSTEM_EMAIL_RECIPIENT", "mehdi.ghribi@soprahr.com")
