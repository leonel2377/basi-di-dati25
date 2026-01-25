"""
Initialize the SQLite database using DB_BasiDiDati.session.sql.
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SQL_PATH = BASE_DIR / "DB_BasiDiDati.session.sql"
DB_PATH = BASE_DIR / "instance" / "flight_booking.db"


def init_db_from_sql():
    if not SQL_PATH.exists():
        raise FileNotFoundError(f"SQL file not found: {SQL_PATH}")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    sql = SQL_PATH.read_text(encoding="utf-8")
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(sql)
        conn.commit()

    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_db_from_sql()
