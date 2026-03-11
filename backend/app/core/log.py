import logging
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _format_details(**details: object) -> str:
    return " ".join(f"{key}={value!r}" for key, value in details.items())


def log_event(
    logger: logging.Logger,
    *,
    stage: str,
    module_file: str,
    function_name: str,
    level: int | None = None,
    exc_info: bool = False,
    **details: object,
) -> None:
    module_path = Path(module_file).resolve()
    folder_name = module_path.parent.name
    file_name = module_path.stem
    detail_text = _format_details(**details)
    message_prefix = f"[DEBUG][{folder_name}/{file_name}/{function_name}]"
    message_body = stage if not detail_text else f"{stage} {detail_text}"
    message = f"{message_prefix} {message_body}"

    if level is None:
        level = logging.ERROR if stage == "ERROR" else logging.INFO

    logger.log(level, message, exc_info=exc_info)
