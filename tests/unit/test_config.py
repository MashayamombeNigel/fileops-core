from pathlib import Path

import pytest

from fileops.config import Config, ConfigError, load_config


def _write_config(tmp_path: Path, content: str) -> Path:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(content)
    return config_file


def test_loads_valid_config_with_only_required_fields(tmp_path: Path) -> None:
    config_file = _write_config(
        tmp_path,
        """
        folder_path: /watched
        log_path: /logs
        """,
    )

    config = load_config(config_file)

    assert config.folder_path == Path("/watched")
    assert config.log_path == Path("/logs")
    assert config.backend == "watchdog"
    assert config.ignore_hidden_files is True


def test_missing_required_field_names_the_field(tmp_path: Path) -> None:
    config_file = _write_config(tmp_path, "log_path: /logs\n")

    with pytest.raises(ConfigError, match="folder_path"):
        load_config(config_file)


def test_wrong_type_for_path_field_is_rejected(tmp_path: Path) -> None:
    config_file = _write_config(
        tmp_path,
        """
        folder_path: 123
        log_path: /logs
        """,
    )

    with pytest.raises(ConfigError, match="folder_path"):
        load_config(config_file)


def test_invalid_yaml_syntax_raises_config_error(tmp_path: Path) -> None:
    config_file = _write_config(tmp_path, "folder_path: [unterminated\n")

    with pytest.raises(ConfigError, match="not valid YAML"):
        load_config(config_file)


def test_empty_config_file_raises_config_error(tmp_path: Path) -> None:
    config_file = _write_config(tmp_path, "")

    with pytest.raises(ConfigError, match="empty"):
        load_config(config_file)


def test_non_mapping_config_raises_config_error(tmp_path: Path) -> None:
    config_file = _write_config(tmp_path, "- just\n- a\n- list\n")

    with pytest.raises(ConfigError, match="mapping"):
        load_config(config_file)


def test_missing_config_file_raises_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Could not read"):
        load_config(tmp_path / "does_not_exist.yaml")


def test_unsafe_yaml_constructs_are_rejected_not_executed(tmp_path: Path) -> None:
    # Guards against the log-injection-adjacent risk in the blueprint's
    # security section: yaml.load with an unsafe loader can instantiate
    # arbitrary Python objects from the config file.
    config_file = _write_config(
        tmp_path,
        """
        folder_path: !!python/object/apply:os.getcwd []
        log_path: /logs
        """,
    )

    with pytest.raises(ConfigError):
        load_config(config_file)


def test_stability_timeout_must_exceed_check_interval(tmp_path: Path) -> None:
    config_file = _write_config(
        tmp_path,
        """
        folder_path: /watched
        log_path: /logs
        stability_check_interval_seconds: 10
        stability_check_timeout_seconds: 5
        """,
    )

    with pytest.raises(ConfigError, match="stability_check_timeout_seconds"):
        load_config(config_file)


def test_tilde_paths_are_expanded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    config_file = _write_config(
        tmp_path,
        """
        folder_path: ~/watched
        log_path: ~/logs
        """,
    )

    config = load_config(config_file)

    assert config.folder_path == tmp_path / "watched"


def test_resolved_db_path_defaults_alongside_logs() -> None:
    config = Config(folder_path=Path("/watched"), log_path=Path("/logs"))

    assert config.resolved_db_path() == Path("/logs/fileops_state.db")


def test_resolved_db_path_honors_explicit_override() -> None:
    config = Config(
        folder_path=Path("/watched"),
        log_path=Path("/logs"),
        db_path=Path("/custom/state.db"),
    )

    assert config.resolved_db_path() == Path("/custom/state.db")


def test_error_message_lists_every_invalid_field(tmp_path: Path) -> None:
    config_file = _write_config(
        tmp_path,
        """
        folder_path: 123
        log_path: 456
        """,
    )

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)

    message = str(exc_info.value)
    assert "folder_path" in message
    assert "log_path" in message
