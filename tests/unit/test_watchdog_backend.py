import time
from pathlib import Path

from fileops.monitor.watchdog_backend import WatchdogBackend


def test_watchdog_detects_new_file(tmp_path: Path) -> None:
    detected_files: list[Path] = []
    
    def on_created(path: Path) -> None:
        detected_files.append(path)
        
    backend = WatchdogBackend(tmp_path, on_created)
    backend.start()
    
    try:
        new_file = tmp_path / "test_file.txt"
        new_file.touch()
        
        time.sleep(0.1)
        
        assert len(detected_files) == 1
        assert detected_files[0] == new_file
    finally:
        backend.stop()

def test_watchdog_ignores_directories(tmp_path: Path) -> None:
    detected_files: list[Path] = []
    
    def on_created(path: Path) -> None:
        detected_files.append(path)
        
    backend = WatchdogBackend(tmp_path, on_created)
    backend.start()
    
    try:
        new_dir = tmp_path / "test_dir"
        new_dir.mkdir()
        
        time.sleep(0.1)
        
        assert len(detected_files) == 0
    finally:
        backend.stop()

def test_watchdog_ignores_hidden_files(tmp_path: Path) -> None:
    detected_files: list[Path] = []
    
    def on_created(path: Path) -> None:
        detected_files.append(path)
        
    backend = WatchdogBackend(tmp_path, on_created)
    backend.start()
    
    try:
        hidden_file = tmp_path / ".hidden_file.txt"
        hidden_file.touch()
        
        time.sleep(0.1)
        
        assert len(detected_files) == 0
    finally:
        backend.stop()
