import logging
from typing import Any
from threading import Thread, Event
from queue import Queue, Empty

from loguru import logger as loguru_logger
import sys

class HadesLogger:
    def __init__(
        self, 
        max_size: int = 15, 
        log_level: str = "INFO"
    ) -> None:
        self._format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        self._queue = Queue(maxsize=max_size)
        self._log_level = log_level.upper()
        self._stop_event = Event()

        self._worker_thread = Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

        logging.getLogger("discord.voice_client").setLevel(logging.WARNING)

        # discord.py-self will scream VC logs without this.

        for logger_name in (
            "discord.http", 
            "discord.client", 
            "discord.gateway", 
            "discord.ext.ipc.server"
        ):
            self._patch_logger(logger_name)

    def _patch_logger(self, logger_name: str) -> None:
        class InterceptHandler(logging.Handler):
            def __init__(self, log_level: str):
                super().__init__()
                self._log_level = log_level

            def emit(self, record: logging.LogRecord) -> None:
                if logging.getLevelName(record.levelname) < logging.getLevelName(self._log_level):
                    return

                loguru_logger.opt(depth=8, exception=record.exc_info).log(record.levelname, record.getMessage())

        logging.getLogger(logger_name).handlers = [InterceptHandler(self._log_level)]  # type: ignore
        logging.getLogger(logger_name).propagate = False

    def _process_queue(self) -> None:
        while not self._stop_event.is_set():
            try:
                record = self._queue.get(timeout=0.1)

                if record is None:
                    return

                if (lvl := loguru_logger.level(record["level"]).no) >= loguru_logger.level(self._log_level).no:
                    loguru_logger.opt(depth=record["depth"]).log(
                        record["level"], record["msg"], *record["args"], **record["kwargs"]
                    )
            except Empty:
                continue
            except Exception as e:
                loguru_logger.error(f"Error in logging thread: {e}")

    def _log(self, level: str, msg: str, *args: Any, **kwargs: Any) -> None:
        if not self._queue.full():
            if loguru_logger.level(level).no < loguru_logger.level(self._log_level).no:
                return

            self._queue.put({
                "level": level, 
                "msg": msg, 
                "args": args, 
                "kwargs": kwargs, 
                "depth": kwargs.pop("depth", 1) + 1
            })
        else:
            loguru_logger.warning("Log queue is full. Dropping message.")

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log("DEBUG", msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log("INFO", msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log("WARNING", msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log("ERROR", msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log("CRITICAL", msg, *args, **kwargs)

    def shutdown(self) -> None:
        self._stop_event.set()
        self._queue.put(None)
        self._worker_thread.join()
