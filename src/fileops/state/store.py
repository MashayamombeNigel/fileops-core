import abc
from typing import Optional
from fileops.events.models import MonitoredFolder, FileEvent, ErrorEvent

class StateStore(abc.ABC):
    @abc.abstractmethod
    def register_folder(self, path: str) -> MonitoredFolder:
        pass

    @abc.abstractmethod
    def get_folder_by_path(self, path: str) -> Optional[MonitoredFolder]:
        pass

    @abc.abstractmethod
    def record_event(self, event: FileEvent) -> bool:
        pass

    @abc.abstractmethod
    def is_file_processed(self, filepath: str, size_bytes: int, file_mtime: float) -> bool:
        pass

    @abc.abstractmethod
    def record_error(self, error: ErrorEvent) -> None:
        pass
