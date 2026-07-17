from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, DirectoryPath, Field, ValidationError

from fileops.exceptions import ConfigError


class Config(BaseModel):
    folder_path: DirectoryPath = Field(
        ...,
        description="Absolute or relative path to the monitored directory."
    )
    log_path: Path = Field(
        ...,
        description="Path where log files (text and JSON) will be written."
    )


def load_config(config_path: str) -> Config:
    path = Path(config_path)
    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(path, encoding="utf-8") as f:
            raw_config: dict[str, Any] | None = yaml.safe_load(f)
            
        if not isinstance(raw_config, dict):
            raise ConfigError("Configuration file must contain a valid YAML dictionary.")
            
        return Config.model_validate(raw_config)
    
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML configuration: {e}") from e
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append(f"Field '{field}': {error['msg']}")
        
        raise ConfigError("Configuration validation failed:\n" + "\n".join(errors)) from e
