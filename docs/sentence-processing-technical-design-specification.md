# Sentence Processing Technical Design Specification

## 1. Scope

This document defines the canonical product semantics for sentence processing in Corpustar, including:

- document deletion behavior
- Analyze workspace initialization on `/analyze/:doc_id`
- frontend initialization and API usage requirements
- socket-driven refresh behavior while keeping UX stable

This specification supersedes any older assumption that Analyze always starts from an empty state.

## 2. Data and Deletion Semantics

### 2.1 Entity Relationship

- `documents` (parent)
- `processings` (child of `documents` by `doc_id`)
- `document_sentences` (child rows bound to both `doc_id` and `processing_id`)

### 2.2 Document Deletion Semantics

When one document is deleted, all related rows for that `doc_id` MUST also be deleted:

- all `processings` rows for that document
- all `document_sentences` rows for that document and its processings

Implementation relies on database foreign key cascade (`ON DELETE CASCADE`) instead of manual row-by-row cleanup logic.

## 3. Analyze Page Initialization Semantics

Route: `/analyze/:doc_id`

### 3.1 Required Initialization Flow

When entering `/analyze/:doc_id` (including route param change), frontend MUST:

1. read `doc_id` from route params
2. load/ensure document base info from `documentStore`
3. call `sentenceStore.initializeAnalyzePage(docId)`

### 3.2 Latest Result Behavior

`initializeAnalyzePage(docId)` MUST query latest successful `sentence_segmentation` snapshot via:

- `GET /api/documents/{doc_id}/sentence-segmentations/latest`

If latest successful result exists:

- show processing/status
- show preview sentence list immediately
- allow loading more immediately via cursor paging

If no successful result exists:

- show explicit empty state
- allow user to trigger `Segment Sentences`

Analyze MUST NOT assume empty state as default when historical successful result exists.

## 4. Frontend Responsibilities

Frontend sentence workspace implementation MUST include:

- `sentenceStore.initializeAnalyzePage(docId)` as the route-entry initializer
- latest segmentation snapshot endpoint integration:
  - `GET /api/documents/{doc_id}/sentence-segmentations/latest`
- sentence cursor paging endpoint integration for existing result continuation:
  - `GET /api/documents/{doc_id}/sentences?processingId=...`

The Analyze detail route is a restore-and-continue workspace, not a forced restart workflow.

## 5. Socket Semantics and Visible Result Strategy

### 5.1 Core Rule

Keep the last successful sentence result visible until a newer processing succeeds and publishes rebuilt list.

### 5.2 Event Handling Rules

- On `processing:created` for current `doc_id`:
  - update processing state to `running`
  - DO NOT clear current visible sentence items

- On `processing:updated` with `state=failed`:
  - keep existing sentence items unchanged
  - update processing state and error message only

- On `sentence:list_rebuilt` for current `doc_id`:
  - load first page for the event `processingId` (`loadInitialSentences(docId, processingId)`)
  - switch visible list to the new processing result

This yields the intended UX:

- entering Analyze first shows old successful result
- re-segmentation running does not cause list flash/empty interruption
- after rebuild, UI switches automatically to newest successful result

## 6. Consistency Notes

Related implementation and checks:

- frontend store: `frontend/src/stores/sentenceStore.ts`
- frontend socket parser: `frontend/src/socket/sentenceSocket.ts`
- latest snapshot API: `backend/app/api/routes.py`
- deletion cascade check: `docs/remove-document-cascade-check.md`
- sentence MVP manual checklist: `docs/sentence-mvp-manual-checklist.md`

