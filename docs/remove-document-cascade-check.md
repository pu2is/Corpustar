# Remove Document Cascade Check

Run from `backend/`:

```powershell
py -3 -m unittest tests.document.remove_document_cascade -v
```

This test uses a real temporary sqlite database file (not repository mocks) and verifies:

1. Create one document.
2. Run sentence segmentation to create at least one processing and at least two sentence rows.
3. Remove the document via `remove_document_with_text_cleanup`.
4. Assert all related data is gone:
   - document row gone
   - `list_processings_by_doc_id(doc_id)` returns empty list
   - `document_sentences` rows by `doc_id` return zero

If this test fails on your machine after schema changes, delete local sqlite file and restart backend to rebuild schema with cascading foreign keys.
