import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.db import (
    DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME,
    DOCUMENT_SENTENCES_TABLE_NAME,
    DOCUMENTS_TABLE_NAME,
    PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME,
    PROCESSINGS_TABLE_NAME,
    get_connection,
    init_db,
)
from app.main import app
from app.services.add_document_service import add_document
from app.services.sentence_edit_service import clip_sentence, merge_sentences
from app.services.sentence_processing_service import segment_document_sentences
from app.services.sentence_segmentation_service import segment_text_to_sentence_spans
from app.socket.socket_events import (
    PROCESSING_CREATED,
    PROCESSING_UPDATED,
    SENTENCE_LIST_REBUILT,
)
from app.socket.socket_publisher import connection_manager as publisher_connection_manager


class SentenceMvpFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._original_db_path = settings.sqlite_database_path
        cls._db_tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        settings.sqlite_database_path = Path(cls._db_tmpdir.name) / "sentence-mvp-tests.sqlite3"
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
            connection.execute(f"DELETE FROM {DOCUMENT_SENTENCES_TABLE_NAME}")
            connection.execute(f"DELETE FROM {PROCESSINGS_TABLE_NAME}")
            connection.execute(f"DELETE FROM {DOCUMENTS_TABLE_NAME}")
            connection.commit()

    def _create_document(self, text: str) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "source.txt"
            source_path.write_text(text, encoding="utf-8")
            document = add_document(str(source_path))
        self._created_text_paths.append(Path(document["textPath"]))
        return document

    def test_init_db_creates_sentence_tables_and_indexes(self) -> None:
        init_db()

        with sqlite3.connect(settings.sqlite_database_path) as connection:
            table_rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
            index_rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()

        tables = {row[0] for row in table_rows}
        indexes = {row[0] for row in index_rows}

        self.assertIn(DOCUMENTS_TABLE_NAME, tables)
        self.assertIn(PROCESSINGS_TABLE_NAME, tables)
        self.assertIn(DOCUMENT_SENTENCES_TABLE_NAME, tables)
        self.assertIn(PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME, indexes)
        self.assertIn(DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME, indexes)

        connection_generator = get_connection()
        connection = next(connection_generator)
        try:
            foreign_keys = connection.execute("PRAGMA foreign_keys;").fetchone()[0]
            self.assertEqual(foreign_keys, 1)
        finally:
            connection_generator.close()

    def test_sentence_segmentation_offsets_are_absolute(self) -> None:
        text = "  Hallo Welt! Wie geht's? Letzte Zeile"
        spans = segment_text_to_sentence_spans(text)

        self.assertEqual(
            spans,
            [
                {"start_offset": 2, "end_offset": 13},
                {"start_offset": 14, "end_offset": 25},
                {"start_offset": 26, "end_offset": 38},
            ],
        )

    def test_segment_api_creates_processing_and_cursor_pagination_works(self) -> None:
        document = self._create_document("A. B. C. D. E.")

        with TestClient(app) as client:
            segmentation_response = client.post(
                f"/api/documents/{document['id']}/sentence-segmentations"
            )
            self.assertEqual(segmentation_response.status_code, 200)
            segmentation_body = segmentation_response.json()

            self.assertEqual(segmentation_body["processing"]["docId"], document["id"])
            self.assertEqual(segmentation_body["processing"]["type"], "sentence_segmentation")
            self.assertEqual(segmentation_body["processing"]["state"], "succeed")
            self.assertEqual(segmentation_body["sentenceCount"], 5)

            processing_id = segmentation_body["processing"]["id"]

            with sqlite3.connect(settings.sqlite_database_path) as connection:
                processing_row = connection.execute(
                    """
                    SELECT doc_id, type, state
                    FROM processings
                    WHERE id = ?
                    """,
                    (processing_id,),
                ).fetchone()
                self.assertIsNotNone(processing_row)
                self.assertEqual(processing_row[0], document["id"])
                self.assertEqual(processing_row[1], "sentence_segmentation")
                self.assertEqual(processing_row[2], "succeed")

                sentence_count_row = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM document_sentences
                    WHERE processing_id = ?
                    """,
                    (processing_id,),
                ).fetchone()
                self.assertIsNotNone(sentence_count_row)
                self.assertEqual(sentence_count_row[0], segmentation_body["sentenceCount"])

            first_page_response = client.get(
                f"/api/documents/{document['id']}/sentences",
                params={
                    "processingId": processing_id,
                    "limit": 2,
                },
            )
            self.assertEqual(first_page_response.status_code, 200)
            first_page = first_page_response.json()
            self.assertEqual(len(first_page["items"]), 2)
            self.assertTrue(first_page["hasMore"])
            self.assertIsInstance(first_page["nextAfterStartOffset"], int)

            next_after = first_page["nextAfterStartOffset"]
            second_page_response = client.get(
                f"/api/documents/{document['id']}/sentences",
                params={
                    "processingId": processing_id,
                    "afterStartOffset": next_after,
                    "limit": 2,
                },
            )
            self.assertEqual(second_page_response.status_code, 200)
            second_page = second_page_response.json()
            self.assertGreaterEqual(len(second_page["items"]), 1)
            self.assertGreater(second_page["items"][0]["startOffset"], next_after)

    def test_merge_validates_sentence_continuity(self) -> None:
        document = self._create_document("One. Two. Three.")
        segmentation = segment_document_sentences(document["id"])
        self.assertEqual(segmentation["sentenceCount"], 3)

        sentence_ids = [
            segmentation["preview"][0]["id"],
            segmentation["preview"][2]["id"],
        ]

        with self.assertRaisesRegex(ValueError, "continuous"):
            merge_sentences(sentence_ids)

    def test_clip_validates_split_offset_range(self) -> None:
        document = self._create_document("Hello world.")
        segmentation = segment_document_sentences(document["id"])
        self.assertEqual(segmentation["sentenceCount"], 1)

        sentence = segmentation["preview"][0]

        with self.assertRaisesRegex(ValueError, "strictly between"):
            clip_sentence(sentence_id=sentence["id"], split_offset=sentence["startOffset"])

        with self.assertRaisesRegex(ValueError, "strictly between"):
            clip_sentence(sentence_id=sentence["id"], split_offset=sentence["endOffset"])

    def test_segmentation_publishes_processing_and_sentence_events(self) -> None:
        document = self._create_document("Alpha. Beta.")
        captured_messages: list[dict] = []

        original_broadcast = publisher_connection_manager.broadcast_json

        async def capture_broadcast(message: dict) -> None:
            captured_messages.append(message)

        publisher_connection_manager.broadcast_json = capture_broadcast
        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/api/documents/{document['id']}/sentence-segmentations"
                )
            self.assertEqual(response.status_code, 200)
            response_body = response.json()
            processing_id = response_body["processing"]["id"]
            sentence_count = response_body["sentenceCount"]
        finally:
            publisher_connection_manager.broadcast_json = original_broadcast

        self.assertEqual(len(captured_messages), 3)
        self.assertEqual(captured_messages[0]["event"], PROCESSING_CREATED)
        self.assertEqual(captured_messages[1]["event"], PROCESSING_UPDATED)
        self.assertEqual(captured_messages[2]["event"], SENTENCE_LIST_REBUILT)

        self.assertEqual(captured_messages[0]["payload"]["docId"], document["id"])
        self.assertEqual(captured_messages[0]["payload"]["processingId"], processing_id)
        self.assertEqual(captured_messages[0]["payload"]["state"], "running")

        self.assertEqual(captured_messages[1]["payload"]["docId"], document["id"])
        self.assertEqual(captured_messages[1]["payload"]["processingId"], processing_id)
        self.assertEqual(captured_messages[1]["payload"]["state"], "succeed")
        self.assertIsNone(captured_messages[1]["payload"]["errorMessage"])

        self.assertEqual(captured_messages[2]["payload"]["docId"], document["id"])
        self.assertEqual(captured_messages[2]["payload"]["processingId"], processing_id)
        self.assertEqual(captured_messages[2]["payload"]["sentenceCount"], sentence_count)


if __name__ == "__main__":
    unittest.main()
