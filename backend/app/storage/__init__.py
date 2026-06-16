import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "readings.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                reading_id TEXT PRIMARY KEY,
                station_id TEXT NOT NULL,
                timestamp  TEXT NOT NULL,
                data       TEXT NOT NULL
            )
        """)


def save(reading: dict) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO readings (reading_id, station_id, timestamp, data) VALUES (?, ?, ?, ?)",
            (reading["reading_id"], reading["station_id"], reading["timestamp"], json.dumps(reading)),
        )


def get_all(station_id: str | None = None, limit: int = 100) -> list[dict]:
    with _conn() as conn:
        if station_id:
            rows = conn.execute(
                "SELECT data FROM readings WHERE station_id = ? ORDER BY timestamp DESC LIMIT ?",
                (station_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT data FROM readings ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [json.loads(r["data"]) for r in rows]


def get_by_id(reading_id: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT data FROM readings WHERE reading_id = ?",
            (reading_id,),
        ).fetchone()
    return json.loads(row["data"]) if row else None


def get_latest(station_id: str | None = None) -> dict | None:
    with _conn() as conn:
        if station_id:
            row = conn.execute(
                "SELECT data FROM readings WHERE station_id = ? ORDER BY timestamp DESC LIMIT 1",
                (station_id,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT data FROM readings ORDER BY timestamp DESC LIMIT 1",
            ).fetchone()
    return json.loads(row["data"]) if row else None
