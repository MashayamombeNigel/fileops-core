from pathlib import Path

import pytest

from fileops.events.models import ErrorEvent, FileEvent
from fileops.state.sqlite_store import SqliteStateStore


@pytest.fixture
def store(tmp_path: Path) -> SqliteStateStore:
    db_path = tmp_path / "test.db"
    return SqliteStateStore(db_path)

def test_register_and_get_folder(store: SqliteStateStore) -> None:
    folder_path = "/var/data/invoices"
    
    folder = store.register_folder(folder_path)
    assert folder.path == folder_path
    assert folder.id is not None
    
    fetched = store.get_folder_by_path(folder_path)
    assert fetched is not None
    assert fetched.id == folder.id
    
    folder_again = store.register_folder(folder_path)
    assert folder_again.id == folder.id

def test_record_and_check_file_event(store: SqliteStateStore) -> None:
    folder = store.register_folder("/var/data")
    
    event = FileEvent(
        folder_id=folder.id,
        filename="report.csv",
        filepath="/var/data/report.csv",
        size_bytes=1024,
        file_mtime=1690000000.0
    )
    
    success = store.record_event(event)
    assert success is True
    
    assert store.is_file_processed("/var/data/report.csv", 1024, 1690000000.0) is True
    
    assert store.is_file_processed("/var/data/report.csv", 2048, 1690000000.0) is False
    assert store.is_file_processed("/var/data/report.csv", 1024, 1690000001.0) is False
    assert store.is_file_processed("/var/data/other.csv", 1024, 1690000000.0) is False

def test_record_error_event(store: SqliteStateStore) -> None:
    folder = store.register_folder("/var/data")
    
    error = ErrorEvent(
        folder_id=folder.id,
        error_type="permission_denied",
        message="Access denied to file.txt"
    )
    
    store.record_error(error)
