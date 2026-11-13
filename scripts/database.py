from pathlib import Path
import sqlite3
from datetime import datetime, timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "processed" / "burnaby_tracker.sqlite"


CREATE_DATASETS_SQL = """
CREATE TABLE IF NOT EXISTS datasets (
    dataset_id INTEGER PRIMARY KEY,
    dataset_name TEXT NOT NULL UNIQUE,
    source TEXT,
    received_date TEXT,
    last_updated TEXT,
    current_status TEXT,
    feature_count INTEGER
);
"""

CREATE_HISTORY_SQL = """
CREATE TABLE IF NOT EXISTS processing_history (
    history_id INTEGER PRIMARY KEY,
    dataset_id INTEGER,
    processing_time TEXT,
    operation TEXT,
    result TEXT,
    message TEXT,
    FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id)
);
"""


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(db_path=DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def init_db(db_path=DB_PATH):
    with connect(db_path) as connection:
        connection.execute(CREATE_DATASETS_SQL)
        connection.execute(CREATE_HISTORY_SQL)
        connection.commit()
    return db_path


def clear_tracker(db_path=DB_PATH):
    """Remove dataset and history rows so a validation run can be repeated."""
    with connect(db_path) as connection:
        connection.execute("DELETE FROM processing_history")
        connection.execute("DELETE FROM datasets")
        connection.commit()


def upsert_dataset(
    dataset_name,
    source,
    received_date,
    current_status,
    feature_count,
    db_path=DB_PATH,
):
    now = utc_now()

    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO datasets (
                dataset_name,
                source,
                received_date,
                last_updated,
                current_status,
                feature_count
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(dataset_name) DO UPDATE SET
                source = excluded.source,
                received_date = excluded.received_date,
                last_updated = excluded.last_updated,
                current_status = excluded.current_status,
                feature_count = excluded.feature_count
            ;
            """,
            (
                dataset_name,
                source,
                received_date,
                now,
                current_status,
                feature_count,
            ),
        )
        connection.commit()

        row = connection.execute(
            """
            SELECT dataset_id
            FROM datasets
            WHERE dataset_name = ?
            """,
            (dataset_name,),
        ).fetchone()

    return int(row["dataset_id"])


def add_history(
    dataset_id,
    operation,
    result,
    message,
    db_path=DB_PATH,
):
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO processing_history (
                dataset_id,
                processing_time,
                operation,
                result,
                message
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                utc_now(),
                operation,
                result,
                message,
            ),
        )
        connection.commit()


def set_status(
    dataset_id,
    current_status,
    feature_count=None,
    db_path=DB_PATH,
):
    now = utc_now()

    with connect(db_path) as connection:
        if feature_count is None:
            connection.execute(
                """
                UPDATE datasets
                SET current_status = ?,
                    last_updated = ?
                WHERE dataset_id = ?
                """,
                (current_status, now, dataset_id),
            )
        else:
            connection.execute(
                """
                UPDATE datasets
                SET current_status = ?,
                    feature_count = ?,
                    last_updated = ?
                WHERE dataset_id = ?
                """,
                (
                    current_status,
                    feature_count,
                    now,
                    dataset_id,
                ),
            )
        connection.commit()
