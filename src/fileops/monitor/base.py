import abc
from pathlib import Path
from typing import Callable

EventHandlerCallable = Callable[[Path], None]

class MonitorBackend(abc.ABC):
    def __init__(self, folder_path: Path, on_created: EventHandlerCallable) -> None:
        self.folder_path = folder_path
        self.on_created = on_created
        self._is_running = False

    @abc.abstractmethod
    def start(self) -> None:
        pass

    @abc.abstractmethod
    def stop(self) -> None:
        pass
