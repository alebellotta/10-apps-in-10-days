import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in payload or key in {
                "args",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            }:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


class StructuredLogger:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._logger.error(message, extra=kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        self._logger.exception(message, extra=kwargs)


def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(logging.getLogger(name))
