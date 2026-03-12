import sqlite3
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.db import init_db
from app.main import app
from app.socket.socket_events import DOCUMENT_CREATED, DOCUMENT_REMOVED
from app.socket.socket_manager import connection_manager
from app.socket.socket_publisher import connection_manager as publisher_connection_manager


class SocketEventFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._original_db_path = settings.sqlite_database_path
        cls._db_tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        settings.sqlite_database_path = Path(cls._db_tmpdir.name) / "socket-tests.sqlite3"
        init_db()

    @classmethod
    def tearDownClass(cls) -> None:
        settings.sqlite_database_path = cls._original_db_path
        cls._db_tmpdir.cleanup()

    def setUp(self) -> None:
        self._created_text_paths: list[Path] = []
        connection_manager.active_connections.clear()
        with sqlite3.connect(settings.sqlite_database_path) as connection:
            connection.execute("DELETE FROM documents")
            connection.commit()

    def tearDown(self) -> None:
        connection_manager.active_connections.clear()
        for text_path in self._created_text_paths:
            text_path.unlink(missing_ok=True)

    def _add_document(self, client: TestClient, source_path: Path) -> dict:
        response = client.post("/api/add_document", json={"filePath": str(source_path)})
        self.assertEqual(response.status_code, 200)
        doc = response.json()
        self._created_text_paths.append(Path(doc["textPath"]))
        return doc

    def test_ws_connect_ping_add_remove_multi_client_sync(self) -> None:
        with TestClient(app) as client:
            with (
                client.websocket_connect("/ws") as ws_a,
                client.websocket_connect("/ws") as ws_b,
            ):
                ws_a.send_text("ping")
                self.assertEqual(ws_a.receive_text(), "pong")

                with tempfile.TemporaryDirectory() as tmpdir:
                    source = Path(tmpdir) / "created.txt"
                    source.write_text(f"created-{uuid4()}", encoding="utf-8")
                    doc = self._add_document(client, source)

                created_a = ws_a.receive_json()
                created_b = ws_b.receive_json()
                expected_created = {"event": DOCUMENT_CREATED, "payload": doc}
                self.assertEqual(created_a, expected_created)
                self.assertEqual(created_b, expected_created)

                # Payload must match current documentStore parser requirements.
                for key in (
                    "id",
                    "filename",
                    "displayName",
                    "fileType",
                    "fileSize",
                    "createdAt",
                    "updatedAt",
                    "note",
                    "sourcePath",
                    "textPath",
                ):
                    self.assertIn(key, doc)

                documents_response = client.get("/api/documents")
                self.assertEqual(documents_response.status_code, 200)
                documents = documents_response.json()
                self.assertTrue(any(item["id"] == doc["id"] for item in documents))

                remove_response = client.delete(f"/api/remove_document/{doc['id']}")
                self.assertEqual(remove_response.status_code, 200)
                self.assertEqual(remove_response.json(), {"success": True, "id": doc["id"]})

                removed_a = ws_a.receive_json()
                removed_b = ws_b.receive_json()
                expected_removed = {
                    "event": DOCUMENT_REMOVED,
                    "payload": {"id": doc["id"]},
                }
                self.assertEqual(removed_a, expected_removed)
                self.assertEqual(removed_b, expected_removed)

    def test_broken_connection_is_cleaned_and_other_client_keeps_receiving(self) -> None:
        with TestClient(app) as client:
            with (
                client.websocket_connect("/ws") as healthy_ws,
                client.websocket_connect("/ws") as flaky_ws,
            ):
                flaky_ws.close()

                with tempfile.TemporaryDirectory() as tmpdir:
                    first_source = Path(tmpdir) / "first.txt"
                    first_source.write_text(f"first-{uuid4()}", encoding="utf-8")
                    first_doc = self._add_document(client, first_source)

                    second_source = Path(tmpdir) / "second.txt"
                    second_source.write_text(f"second-{uuid4()}", encoding="utf-8")
                    second_doc = self._add_document(client, second_source)

                first_event = healthy_ws.receive_json()
                second_event = healthy_ws.receive_json()
                self.assertEqual(first_event, {"event": DOCUMENT_CREATED, "payload": first_doc})
                self.assertEqual(second_event, {"event": DOCUMENT_CREATED, "payload": second_doc})
                self.assertEqual(len(connection_manager.active_connections), 1)

    def test_broadcast_failure_does_not_break_http_success(self) -> None:
        original_broadcast = publisher_connection_manager.broadcast_json

        async def always_fail_broadcast(_: dict) -> None:
            raise RuntimeError("forced publish failure")

        publisher_connection_manager.broadcast_json = always_fail_broadcast
        try:
            with TestClient(app) as client:
                with tempfile.TemporaryDirectory() as tmpdir:
                    source = Path(tmpdir) / "failure-case.txt"
                    source.write_text(f"failure-{uuid4()}", encoding="utf-8")
                    add_response = client.post("/api/add_document", json={"filePath": str(source)})
                self.assertEqual(add_response.status_code, 200)
                doc = add_response.json()
                self._created_text_paths.append(Path(doc["textPath"]))

                remove_response = client.delete(f"/api/remove_document/{doc['id']}")
                self.assertEqual(remove_response.status_code, 200)
                self.assertEqual(remove_response.json(), {"success": True, "id": doc["id"]})
        finally:
            publisher_connection_manager.broadcast_json = original_broadcast


if __name__ == "__main__":
    unittest.main()
