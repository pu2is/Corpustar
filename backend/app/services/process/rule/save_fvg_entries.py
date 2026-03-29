from uuid import uuid4

from app.core.process.fvg_entries.prelabel import FvgPrelabel
from app.core.process.worker.accelerate_io import accelerate_io
from app.core.rules.fvg_csv_reader import read_fvg_csv
from app.core.rules.rule_utils import calculate_rule_id, resolve_rule_path, validate_rule_type
from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories.fvg_entries import save_fvg_entries_in_batch
from app.infrastructure.repositories.rules import get_existing_rule_for_import, write_rule_item


_PRELABEL = FvgPrelabel()


def prelable_fvg_entries(csv_path: str) -> list[dict[str, str]]:
    parsed_rows = read_fvg_csv(csv_path)
    labeled_rows = _PRELABEL.label(parsed_rows)
    return labeled_rows


def save_fvg_entries(*, process_id: str, path: str, rule_type: str) -> dict[str, object]:
    normalized_rule_type = validate_rule_type(rule_type)
    resolved_csv_path = resolve_rule_path(path)
    rule_id = calculate_rule_id(resolved_csv_path)

    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")

            existing_rule = get_existing_rule_for_import(
                rule_id=rule_id,
                rule_type=normalized_rule_type,
                path=resolved_csv_path,
                connection=connection,
            )
            if existing_rule is not None:
                raise ValueError(f"Rule already exists for hash: {rule_id}")

            labeled_rows = prelable_fvg_entries(resolved_csv_path)
            # Lightweight parallel mapping for UUID assignment / row normalization.
            def _build_row(item: object) -> object:
                row = item  # type: ignore[assignment]
                return {
                    "id": str(uuid4()),
                    "rule_id": rule_id,
                    "verb": str(row["verb"]),
                    "phrase": str(row["phrase"]),
                    "noun": str(row["noun"]),
                    "prep": str(row["prep"]),
                    "structure_type": str(row["structure_type"]),
                    "semantic_type": str(row["semantic_type"]),
                }

            fvg_entries = accelerate_io(_build_row, labeled_rows)

            rule_item = write_rule_item(
                {
                    "id": rule_id,
                    "version_id": process_id,
                    "type": normalized_rule_type,
                    "path": resolved_csv_path,
                },
                connection=connection,
            )

            saved_entries = save_fvg_entries_in_batch(
                fvg_entries,  # type: ignore[arg-type]
                connection=connection,
            )

            connection.commit()
            return {
                "rule": rule_item,
                "fvg_entries": saved_entries,
            }
        except Exception:
            connection.rollback()
            raise
