import logging
import logging.config
from logging.handlers import RotatingFileHandler
from pathlib import Path
import structlog
import sys

def setup_logging(log_dir: Path, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5) -> None:
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    text_log_path = log_dir / "fileops.log"
    json_log_path = log_dir / "fileops.jsonl"

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter_text = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=False),
        foreign_pre_chain=shared_processors,
    )
    
    formatter_json = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    text_handler = RotatingFileHandler(
        text_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    text_handler.setFormatter(formatter_text)

    json_handler = RotatingFileHandler(
        json_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    json_handler.setFormatter(formatter_json)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter_text)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    
    root_logger.addHandler(text_handler)
    root_logger.addHandler(json_handler)
    # Note: We omit console_handler from root to prevent duplicate logs with Typer Rich console.
    # Typer CLI output is handled manually, but we can enable console_handler if needed later.
