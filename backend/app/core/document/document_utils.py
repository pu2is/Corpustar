import hashlib
from pathlib import Path

from app.core.log import get_logger, log_event

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def get_file_type(file_path: str) -> str:
    function_name = "get_file_type"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        file_path=file_path,
    )

    try:
        extension = Path(file_path).suffix.lower()
        file_type_map = {
            ".doc": "doc",
            ".docx": "docx",
            ".odt": "odt",
            ".txt": "txt",
        }

        if extension not in file_type_map:
            raise ValueError(f"Unsupported file type: {extension}")

        file_type = file_type_map[extension]
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            extension=extension,
            result=file_type,
        )
        return file_type
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            file_path=file_path,
            error=str(error),
            exc_info=True,
        )
        raise


def calculate_sha256(file_path: str) -> str:
    function_name = "calculate_sha256"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        file_path=file_path,
    )

    try:
        data = Path(file_path).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            bytes_count=len(data),
            result=digest,
        )
        return digest
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            file_path=file_path,
            error=str(error),
            exc_info=True,
        )
        raise


def get_file_size(file_path: str) -> int:
    function_name = "get_file_size"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        file_path=file_path,
    )

    try:
        file_size = Path(file_path).stat().st_size
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=file_size,
        )
        return file_size
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            file_path=file_path,
            error=str(error),
            exc_info=True,
        )
        raise


def ensure_storage_dir() -> Path:
    function_name = "ensure_storage_dir"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )

    try:
        storage_dir = Path(__file__).resolve().parents[3] / "storage" / "texts"
        storage_dir.mkdir(parents=True, exist_ok=True)
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=storage_dir.as_posix(),
        )
        return storage_dir
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            error=str(error),
            exc_info=True,
        )
        raise
