import json
from pathlib import Path
import structlog

from fileops.logging_setup import setup_logging

def test_logging_generates_both_formats(tmp_path: Path) -> None:
    setup_logging(tmp_path)
    
    logger = structlog.get_logger("test_logger")
    logger.info("test_event", custom_field="value123")
    
    text_log = (tmp_path / "fileops.log").read_text(encoding="utf-8")
    json_log = (tmp_path / "fileops.jsonl").read_text(encoding="utf-8")
    
    assert "test_event" in text_log
    assert "value123" in text_log
    
    parsed = json.loads(json_log.strip())
    assert parsed["event"] == "test_event"
    assert parsed["custom_field"] == "value123"
    assert "timestamp" in parsed
    assert parsed["logger"] == "test_logger"
