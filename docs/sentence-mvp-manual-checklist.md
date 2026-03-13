# Sentence Processing MVP - Minimal Self-Check

## Backend Automated Checks

Run from `backend/`:

```powershell
py -3 -m unittest tests.sentence.test_sentence_mvp_flow -v
```

Covered by this test module:

- `init_db` creates `documents`, `processings`, `document_sentences` and required indexes.
- SQLite connection created by `get_connection` enables `PRAGMA foreign_keys = ON`.
- Sentence segmentation offsets are deterministic and absolute.
- `POST /api/documents/{doc_id}/sentence-segmentations` creates processing + sentence rows.
- Cursor pagination returns ordered slices with `afterStartOffset`.
- Merge rejects non-continuous sentence selections.
- Clip rejects invalid `splitOffset` at sentence boundaries.
- Segmentation emits socket envelopes:
  - `processing:created`
  - `processing:updated`
  - `sentence:list_rebuilt`

## Frontend Manual Checklist

Preconditions:

- Backend is running.
- Frontend is running.
- At least one document exists and can open `DocumentDetail`.
- Browser devtools console has no blocking runtime errors.

Checklist:

1. Open `DocumentDetail` for one document.
Expected:
- Document base info is visible.
- Sentence workspace components render (status bar, toolbar, list area).

2. Click `Segment Sentences`.
Expected:
- Processing status appears with `state=running` then `state=succeed`.
- Sentences appear without manual page refresh.

3. Validate auto-refresh via websocket event.
Expected:
- After segmentation finishes, sentence list refreshes automatically.
- No manual reload is needed.

4. Click `Load More` when `hasMore=true`.
Expected:
- More sentence rows append.
- Order remains by `startOffset` ascending.

5. Select at least 2 adjacent sentences and click `Merge Selected`.
Expected:
- Request succeeds.
- List reloads first page for current processing.
- Total sentence count effectively decreases by 1 after reload.

6. Click `Clip` on one sentence and enter a valid split offset inside `(startOffset, endOffset)`.
Expected:
- Request succeeds.
- List reloads first page.
- The old sentence is replaced by 2 new sentences (net +1 sentence).

7. Negative clip check: use `splitOffset == startOffset` or `splitOffset == endOffset`.
Expected:
- API returns validation error.
- UI shows error state/message and sentence list remains unchanged.

8. Negative merge check: select non-continuous sentences.
Expected:
- API returns validation error.
- UI shows error state/message and sentence list remains unchanged.

