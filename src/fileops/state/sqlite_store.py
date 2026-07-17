import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from fileops.events.models import MonitoredFolder, FileEvent, ErrorEvent
from fileops.state.store import StateStore
from fileops.exceptions import FileOpsError

def adapt_datetime_iso(val: datetime) -> str:
    return val.isoformat()

def convert_datetime(val: bytes) -> datetime:
    return datetime.fromisoformat(val.decode("utf-8"))

sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("TIMESTAMP", convert_datetime)


class StateStoreError(FileOpsError):
    pass


class SqliteStateStore(StateStore):
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(
                self.db_path, 
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            return conn
        except sqlite3.Error as e:
            raise StateStoreError(f"Failed to connect to SQLite: {e}")

    def _init_db(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS monitored_folders (
            id TEXT PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS file_events (
            event_id TEXT PRIMARY KEY,
            folder_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
            extension TEXT,
            file_hash TEXT,
            file_mtime REAL NOT NULL,
            detected_at TIMESTAMP NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (folder_id) REFERENCES monitored_folders(id)
        );

        CREATE INDEX IF NOT EXISTS idx_file_events_folder_detected 
            ON file_events(folder_id, detected_at);
            
        CREATE INDEX IF NOT EXISTS idx_file_events_filepath 
            ON file_events(filepath);

        CREATE TABLE IF NOT EXISTS error_events (
            error_id TEXT PRIMARY KEY,
            folder_id TEXT NOT NULL,
            event_id TEXT,
            error_type TEXT NOT NULL,
            message TEXT NOT NULL,
            occurred_at TIMESTAMP NOT NULL,
            FOREIGN KEY (folder_id) REFERENCES monitored_folders(id),
            FOREIGN KEY (event_id) REFERENCES file_events(event_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_error_events_folder_occurred
            ON error_events(folder_id, occurred_at);
        """
        
        with self._get_connection() as conn:
            try:
                conn.executescript(schema)
            except sqlite3.Error as e:
                raise StateStoreError(f"Failed to initialize SQLite schema: {e}")

    def register_folder(self, path: str) -> MonitoredFolder:
        folder = self.get_folder_by_path(path)
        if folder:
            return folder
            
        folder = MonitoredFolder(path=path)
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO monitored_folders (id, path, is_active, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (folder.id, folder.path, folder.is_active, folder.created_at)
            )
        return folder

    def get_folder_by_path(self, path: str) -> Optional[MonitoredFolder]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM monitored_folders WHERE path = ?", (path,)
            ).fetchone()
            
            if row:
                return MonitoredFolder(**dict(row))
        return None

    def record_event(self, event: FileEvent) -> bool:
        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO file_events 
                    (event_id, folder_id, filename, filepath, size_bytes, extension, file_hash, file_mtime, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id, event.folder_id, event.filename, event.filepath,
                        event.size_bytes, event.extension, event.file_hash, 
                        event.file_mtime, event.detected_at
                    )
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def is_file_processed(self, filepath: str, size_bytes: int, file_mtime: float) -> bool:
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT 1 FROM file_events 
                WHERE filepath = ? AND size_bytes = ? AND file_mtime = ?
                LIMIT 1
                """,
                (filepath, size_bytes, file_mtime)
            ).fetchone()
            return row is not None

    def record_error(self, error: ErrorEvent) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO error_events 
                (error_id, folder_id, event_id, error_type, message, occurred_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    error.error_id, error.folder_id, error.event_id, 
                    error.error_type, error.message, error.occurred_at
                )
            )
