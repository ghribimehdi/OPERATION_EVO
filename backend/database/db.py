import os
import sqlite3
from pathlib import Path
from config import Config

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Config.SQLITE_DB_PATH_STR
SCHEMA_PATH = BASE_DIR / 'database' / 'init_db.sql'


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(force=False):
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)

    if force and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    return DB_PATH
