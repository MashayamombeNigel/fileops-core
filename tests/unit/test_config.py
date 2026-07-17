from pathlib import Path

import pytest
import yaml

from fileops.config import load_config
from fileops.exceptions import ConfigError


def test_load_valid_config(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    watched_dir = tmp_path / "watched"
    watched_dir.mkdir()
    
    config_data = {
        "folder_path": str(watched_dir),
        "log_path": "/var/log/fileops"
    }
    config_file.write_text(yaml.dump(config_data))
    
    config = load_config(str(config_file))
    
    assert str(config.folder_path) == str(watched_dir)
    assert config.log_path.as_posix() == "/var/log/fileops"


def test_missing_config_file() -> None:
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config("does_not_exist.yaml")


def test_invalid_yaml(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("folder_path: [unclosed list")
    
    with pytest.raises(ConfigError, match="Failed to parse YAML configuration"):
        load_config(str(config_file))


def test_missing_required_field(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("log_path: /var/log/fileops\n")
    
    with pytest.raises(ConfigError, match="Field 'folder_path': Field required"):
        load_config(str(config_file))


def test_invalid_folder_path(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_data = {
        "folder_path": "/path/that/definitely/does/not/exist/999",
        "log_path": "/var/log/fileops"
    }
    config_file.write_text(yaml.dump(config_data))
    
    with pytest.raises(ConfigError, match="Path does not point to a directory"):
        load_config(str(config_file))
