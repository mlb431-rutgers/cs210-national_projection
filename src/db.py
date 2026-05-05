import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db" / "projection.db"
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"
DATA_DIR = PROJECT_ROOT / "data"

BASE_YEAR = 2023
PROJECTION_YEARS = (2028, 2033, 2038, 2043, 2048, 2053, 2058)


def get_connection(read_only: bool = False) -> sqlite3.Connection:
    if read_only:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
    return conn
