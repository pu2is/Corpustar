from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from app.core.document.document_utils import get_file_type
from app.core.log import get_logger, log_event

LOGGER = get_logger(__name__)
MODULE_FILE = __file__
ODT_TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "iso-8859-1")
LIBREOFFICE_BINARIES = ("soffice", "libreoffice")


def convert_document_to_text(file_path: str) -> str:
    function_name = "convert_document_to_text"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        file_path=file_path,
    )

    try:
        file_type = get_file_type(file_path)

        if file_type == "txt":
            text = _read_txt(file_path)
        elif file_type == "docx":
            text = _read_docx(file_path)
        elif file_type == "odt":
            text = _read_odt(file_path)
        elif file_type == "doc":
            text = _read_doc(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            file_type=file_type,
            result_length=len(text),
        )
        return text
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


def _read_txt(file_path: str) -> str:
    return _decode_text_bytes(Path(file_path).read_bytes())


def _read_doc(file_path: str) -> str:
    extractor_errors = []

    for extractor in (
        _read_doc_with_libreoffice,
        _read_doc_with_antiword,
        _read_doc_with_catdoc,
    ):
        try:
            text = extractor(file_path)
            if text.strip():
                return text
            extractor_errors.append(f"{extractor.__name__}: empty output")
        except Exception as error:  # pragma: no cover - best effort by environment
            extractor_errors.append(f"{extractor.__name__}: {error}")

    raise RuntimeError(
        "Unable to convert .doc file. "
        "Install LibreOffice, antiword, or catdoc. "
        f"Details: {'; '.join(extractor_errors)}"
    )


def _read_docx(file_path: str) -> str:
    try:
        from docx import Document
    except ImportError as error:
        raise RuntimeError(
            "python-docx is required for .docx conversion. Install it with 'pip install python-docx'."
        ) from error

    document = Document(file_path)
    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def _read_odt(file_path: str) -> str:
    with zipfile.ZipFile(file_path) as archive:
        content_xml = archive.read("content.xml")

    root = ET.fromstring(content_xml)
    paragraph_tags = {f"{{{ODT_TEXT_NS}}}p", f"{{{ODT_TEXT_NS}}}h"}
    paragraphs = []

    for element in root.iter():
        if element.tag not in paragraph_tags:
            continue

        text = "".join(element.itertext()).strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def _read_doc_with_libreoffice(file_path: str) -> str:
    office_binary = next(
        (binary for binary in LIBREOFFICE_BINARIES if shutil.which(binary)),
        None,
    )
    if office_binary is None:
        raise RuntimeError("LibreOffice binary not found")

    source_path = Path(file_path).resolve()
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [
                office_binary,
                "--headless",
                "--convert-to",
                "txt:Text",
                "--outdir",
                temp_dir,
                source_path.as_posix(),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            stderr_text = _decode_text_bytes(result.stderr).strip()
            raise RuntimeError(f"{office_binary} failed ({result.returncode}): {stderr_text}")

        txt_candidates = list(Path(temp_dir).glob("*.txt"))
        if not txt_candidates:
            raise RuntimeError("LibreOffice did not produce a .txt file")

        return _read_txt(txt_candidates[0].as_posix())


def _read_doc_with_antiword(file_path: str) -> str:
    antiword_binary = shutil.which("antiword")
    if antiword_binary is None:
        raise RuntimeError("antiword binary not found")

    result = subprocess.run(
        [antiword_binary, file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        stderr_text = _decode_text_bytes(result.stderr).strip()
        raise RuntimeError(f"antiword failed ({result.returncode}): {stderr_text}")

    return _decode_text_bytes(result.stdout)


def _read_doc_with_catdoc(file_path: str) -> str:
    catdoc_binary = shutil.which("catdoc")
    if catdoc_binary is None:
        raise RuntimeError("catdoc binary not found")

    command_variants = (
        [catdoc_binary, "-d", "utf-8", file_path],
        [catdoc_binary, file_path],
    )
    for command in command_variants:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return _decode_text_bytes(result.stdout)

    stderr_text = _decode_text_bytes(result.stderr).strip()
    raise RuntimeError(f"catdoc failed ({result.returncode}): {stderr_text}")


def _decode_text_bytes(raw_bytes: bytes) -> str:
    for encoding in TEXT_ENCODINGS:
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue

    return raw_bytes.decode("utf-8", errors="replace")
