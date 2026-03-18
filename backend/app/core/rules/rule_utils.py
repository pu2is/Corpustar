import hashlib
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

SUPPORTED_RULE_TYPE = "fvg"


def _normalize_frontend_path(path: str) -> Path:
    raw_path = path.strip()
    if not raw_path:
        raise ValueError("Rule CSV path is required")

    parsed_path = urlparse(raw_path)
    if parsed_path.scheme != "file":
        return Path(raw_path)

    uri_path = parsed_path.path
    if parsed_path.netloc and parsed_path.netloc.lower() != "localhost":
        uri_path = f"//{parsed_path.netloc}{uri_path}"

    local_path = url2pathname(unquote(uri_path))
    if not local_path:
        raise ValueError("Invalid file URI for rule CSV path")

    return Path(local_path)


def resolve_rule_path(path: str) -> str:
    candidate_path = _normalize_frontend_path(path)
    resolved_path = candidate_path.expanduser().resolve(strict=True)

    if not resolved_path.is_file():
        raise ValueError(f"Rule CSV path is not a file: {resolved_path}")

    return resolved_path.as_posix()


def calculate_rule_id(path: str) -> str:
    resolved_path = resolve_rule_path(path)
    csv_bytes = Path(resolved_path).read_bytes()
    return hashlib.sha256(csv_bytes).hexdigest()


def validate_rule_type(rule_type: str) -> str:
    normalized_type = rule_type.strip().lower()
    if normalized_type != SUPPORTED_RULE_TYPE:
        raise ValueError(f"Unsupported rule type: {rule_type}")

    return normalized_type
