import csv
from pathlib import Path


def read_fvg_csv(path: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    csv_path = Path(path)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        for row_number, row in enumerate(reader, start=1):
            if len(row) < 2:
                raise ValueError(
                    f"Malformed FVG CSV row {row_number}: expected at least 2 columns"
                )

            verb = row[0].strip()
            phrase = row[1].strip()

            if not verb:
                raise ValueError(f"Invalid FVG CSV row {row_number}: verb is empty")
            if not phrase:
                raise ValueError(f"Invalid FVG CSV row {row_number}: phrase is empty")

            extra_meaningful_columns = [
                value for value in row[2:] if value.strip()
            ]
            if extra_meaningful_columns:
                raise ValueError(
                    f"Malformed FVG CSV row {row_number}: unexpected extra columns"
                )

            rows.append({"verb": verb, "phrase": phrase})

    return rows
