import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.core.config import settings
from app.core.db import init_db
from app.services.add_document_service import add_document
from app.services.document_repository import get_document_by_id
from app.services.processing_repository import list_processings_by_doc_id
from app.services.remove_document_service import remove_document_with_text_cleanup
from app.services.sentence_processing_service import segment_document_sentences


class RemoveDocumentCascadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._original_db_path = settings.sqlite_database_path
        cls._db_tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        settings.sqlite_database_path = Path(cls._db_tmpdir.name) / "remove-cascade-tests.sqlite3"
        init_db()

    @classmethod
    def tearDownClass(cls) -> None:
        settings.sqlite_database_path = cls._original_db_path
        cls._db_tmpdir.cleanup()

    def setUp(self) -> None:
        self._created_text_paths: list[Path] = []
        self._clear_tables()

    def tearDown(self) -> None:
        self._clear_tables()
        for text_path in self._created_text_paths:
            text_path.unlink(missing_ok=True)

    def _clear_tables(self) -> None:
        with sqlite3.connect(settings.sqlite_database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON;")
            connection.execute("DELETE FROM document_sentences")
            connection.execute("DELETE FROM processings")
            connection.execute("DELETE FROM documents")
            connection.commit()

    def _create_document(self, text: str) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "source.txt"
            source_path.write_text(text, encoding="utf-8")
            document = add_document(str(source_path))
        self._created_text_paths.append(Path(document["textPath"]))
        return document

    def test_remove_document_cascades_processings_and_sentences(self) -> None:
        document = self._create_document("First sentence. Second sentence.")
        segmentation = segment_document_sentences(document["id"])
        self.assertGreaterEqual(segmentation["sentenceCount"], 2)

        processing_id = segmentation["processing"]["id"]

        processings_before_delete = list_processings_by_doc_id(document["id"])
        self.assertGreaterEqual(len(processings_before_delete), 1)

        with sqlite3.connect(settings.sqlite_database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON;")
            sentence_doc_count_before = connection.execute(
                "SELECT COUNT(*) FROM document_sentences WHERE doc_id = ?",
                (document["id"],),
            ).fetchone()[0]
        self.assertGreaterEqual(sentence_doc_count_before, 2)

        result = remove_document_with_text_cleanup(document["id"])
        self.assertTrue(result["success"])
        self.assertEqual(result["id"], document["id"])

        # 1) document gone
        self.assertIsNone(get_document_by_id(document["id"]))
        # 2) processings by doc_id gone
        self.assertEqual(list_processings_by_doc_id(document["id"]), [])

        with sqlite3.connect(settings.sqlite_database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON;")

            document_count = connection.execute(
                "SELECT COUNT(*) FROM documents WHERE id = ?",
                (document["id"],),
            ).fetchone()[0]
            processing_count = connection.execute(
                "SELECT COUNT(*) FROM processings WHERE doc_id = ?",
                (document["id"],),
            ).fetchone()[0]
            sentence_doc_count = connection.execute(
                "SELECT COUNT(*) FROM document_sentences WHERE doc_id = ?",
                (document["id"],),
            ).fetchone()[0]
            sentence_processing_count = connection.execute(
                "SELECT COUNT(*) FROM document_sentences WHERE processing_id = ?",
                (processing_id,),
            ).fetchone()[0]

        self.assertEqual(document_count, 0)
        self.assertEqual(processing_count, 0)
        self.assertEqual(sentence_doc_count, 0)
        self.assertEqual(sentence_processing_count, 0)


if __name__ == "__main__":
    unittest.main()
