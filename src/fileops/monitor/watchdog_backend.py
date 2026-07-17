import logging
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from fileops.monitor.base import EventHandlerCallable, MonitorBackend

logger = logging.getLogger(__name__)


class FileCreateHandler(FileSystemEventHandler):
    def __init__(self, callback: EventHandlerCallable) -> None:
        self.callback = callback
        super().__init__()

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
            
        path = Path(event.src_path)
        
        if path.name.startswith("."):
            return
            
        self.callback(path)


class WatchdogBackend(MonitorBackend):
    def __init__(self, folder_path: Path, on_created: EventHandlerCallable) -> None:
        super().__init__(folder_path, on_created)
        self._observer = Observer()
        self._handler = FileCreateHandler(self.on_created)

    def start(self) -> None:
        if self._is_running:
            return
            
        self._observer.schedule(  # type: ignore[no-untyped-call]
            self._handler, 
            str(self.folder_path), 
            recursive=False
        )
        self._observer.start()  # type: ignore[no-untyped-call]
        self._is_running = True
        logger.debug(f"WatchdogBackend started monitoring {self.folder_path}")

    def stop(self) -> None:
        if not self._is_running:
            return
            
        self._observer.stop()  # type: ignore[no-untyped-call]
        self._observer.join()
        self._is_running = False
        logger.debug("WatchdogBackend stopped")
