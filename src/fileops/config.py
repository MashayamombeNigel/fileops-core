from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, ValidationInfo, field_validator


class ConfigError(Exception):
    """Raised when config.yaml cannot be read or fails schema validation."""


class Config(BaseModel):
    folder_path: Path
    log_path: Path

    # Defaults to a file alongside the logs rather than inside the monitored
    # folder itself: the state store is operational metadata about the tool,
    # not something the client's folder should ever contain.
    db_path: Path | None = None

    backend: Literal["watchdog", "polling"] = "watchdog"
    polling_interval_seconds: float = Field(default=5.0, gt=0)
    ignore_hidden_files: bool = True

    stability_check_interval_seconds: float = Field(default=1.0, gt=0)
    stability_check_timeout_seconds: float = Field(default=30.0, gt=0)

    log_rotation_max_bytes: int = Field(default=10_000_000, gt=0)
    log_rotation_backup_count: int = Field(default=5, ge=0)

    heartbeat_interval_seconds: int = Field(default=3600, gt=0)
    state_retention_days: int = Field(default=30, gt=0)

    @field_validator("folder_path", "log_path", "db_path", mode="before")
    @classmethod
    def _coerce_and_expand_path(cls, value: Any) -> Path | None:
        if value is None:
            return None
        if not isinstance(value, (str, Path)):
            # pydantic only wraps ValueError/AssertionError from validators into
            # ValidationError; a raw TypeError would be treated as a bug in this
            # validator itself and propagate uncaught.
            raise ValueError(f"expected a path string, got {type(value).__name__}")
        return Path(value).expanduser()

    @field_validator("stability_check_timeout_seconds")
    @classmethod
    def _timeout_must_exceed_check_interval(cls, value: float, info: ValidationInfo) -> float:
        interval = info.data.get("stability_check_interval_seconds")
        # A timeout at or below the polling interval would mean a file could
        # never survive even one stability check before being timed out.
        if interval is not None and value <= interval:
            raise ValueError(
                "stability_check_timeout_seconds must be greater than "
                "stability_check_interval_seconds"
            )
        return value

    def resolved_db_path(self) -> Path:
        return self.db_path or self.log_path / "fileops_state.db"


def load_config(path: Path) -> Config:
    try:
        raw_text = path.read_text()
    except OSError as exc:
        raise ConfigError(f"Could not read config file at {path}: {exc}") from exc

    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Config file at {path} is not valid YAML: {exc}") from exc

    if data is None:
        raise ConfigError(f"Config file at {path} is empty")

    if not isinstance(data, dict):
        raise ConfigError(
            f"Config file at {path} must define a mapping of settings, "
            f"got {type(data).__name__}"
        )

    try:
        return Config.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(path, exc)) from exc


def _format_validation_error(path: Path, exc: ValidationError) -> str:
    lines = [f"Invalid configuration in {path}:"]
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"])
        lines.append(f"  - {field}: {error['msg']}")
    return "\n".join(lines)
