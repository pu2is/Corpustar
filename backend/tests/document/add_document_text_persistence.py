import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.infrastructure.db import apply_migrations, init_schema
from app.services.add_document_service import add_document


class AddDocumentTextPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._original_db_path = settings.sqlite_database_path
        cls._db_tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        settings.sqlite_database_path = Path(cls._db_tmpdir.name) / "test.sqlite3"
        apply_migrations()
        init_schema()
        cls._expected_text_dir = (
            Path(__file__).resolve().parents[2] / "storage" / "texts"
        ).resolve()

    @classmethod
    def tearDownClass(cls) -> None:
        settings.sqlite_database_path = cls._original_db_path
        cls._db_tmpdir.cleanup()

    def _get_db_text_path(self, doc_id: str) -> str:
        with sqlite3.connect(settings.sqlite_database_path) as connection:
            row = connection.execute(
                "SELECT text_path FROM documents WHERE id = ?",
                (doc_id,),
            ).fetchone()

        self.assertIsNotNone(row, "documents row should exist after add_document")
        return row[0]

    def test_add_document_odt_uses_storage_text_and_removes_legacy_sibling_txt(self) -> None:
        unique_text = f"odt-case-{uuid4()}"
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "sample.odt"
            legacy_sibling_txt = source_path.with_suffix(".txt")

            content_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
    <office:body>
        <office:text>
            <text:p>{unique_text}</text:p>
        </office:text>
    </office:body>
</office:document-content>
"""
            with zipfile.ZipFile(source_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("content.xml", content_xml)
            legacy_sibling_txt.write_text("legacy sidecar", encoding="utf-8")

            result = add_document(str(source_path))
            text_path = Path(result["textPath"]).resolve()
            self.addCleanup(text_path.unlink, missing_ok=True)

            self.assertEqual(text_path.parent, self._expected_text_dir)
            self.assertEqual(text_path.name, f"{result['id']}.txt")
            self.assertTrue(text_path.exists())
            self.assertFalse(
                legacy_sibling_txt.exists(),
                "source sibling .txt should not remain after non-txt import",
            )

            db_text_path = self._get_db_text_path(result["id"])
            self.assertEqual(Path(db_text_path).resolve(), text_path)

    def test_add_document_txt_keeps_original_source_file(self) -> None:
        source_content = f"txt-source-{uuid4()}"
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "original.txt"
            source_path.write_text(source_content, encoding="utf-8")

            result = add_document(str(source_path))
            text_path = Path(result["textPath"]).resolve()
            self.addCleanup(text_path.unlink, missing_ok=True)

            self.assertTrue(source_path.exists(), "original txt source file must be kept")
            self.assertEqual(source_path.read_text(encoding="utf-8"), source_content)
            self.assertEqual(text_path.parent, self._expected_text_dir)
            self.assertTrue(text_path.exists())

            db_text_path = self._get_db_text_path(result["id"])
            self.assertEqual(Path(db_text_path).resolve(), text_path)


if __name__ == "__main__":
    unittest.main()
