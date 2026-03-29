# Socket Events Contract

Canonical event names are defined in:

- Backend: `backend/app/socket/socket_events.py`
- Frontend: `frontend/src/socket/events.ts`

Payloads are broadcast by backend services and are currently mostly `snake_case` dictionaries.

## Canonical Events

| Event | Payload |
| --- | --- |
| `socket:connected` | client-local signal, no backend payload |
| `socket:disconnected` | client-local signal, no backend payload |
| `document:created` | document item object |
| `document:removed` | `{ "id": string }` |
| `segmentation:started` | processing item object |
| `segmentation:failed` | processing item object |
| `segmentation:succeed` | `{ "processing": processing item, "preview": sentence item[] }` |
| `lemmatize:started` | processing item object |
| `lemmatize:failed` | processing item object |
| `lemmatize:succeed` | processing item object |
| `importRule:started` | processing item object |
| `importRule:failed` | processing item object |
| `importRule:succeed` | `{ "processing": processing item, "rule": rule item }` |
| `importFvgEntries:succeed` | `{ "ok": boolean }` |
| `sentence:merged` | sentence item object |
| `sentence:clipped` | sentence item[] |
| `sentence:corrected` | sentence item object |
| `rule:removed` | rule item object |
| `fvg:appended` | fvg entry item object |
| `fvg:removed` | `{ "id": string, "rule_id": string }` |
| `fvg:updated` | fvg entry item object |

## Compatibility Layer (Stage B)

`frontend/src/socket/socket.ts` dispatches canonical events and also legacy aliases:

- `segmentation:started -> process:created`
- `segmentation:succeed -> process:updated`
- `segmentation:failed -> process:updated`
- `importRule:succeed -> rule:created`
- `importFvgEntries:succeed -> fvgRules:created`
- `fvg:appended -> fvgRule:appended`
- `fvg:removed -> fvgRule:removed`
- `fvg:updated -> fvgRule:updated`
- `lemmatize:succeed -> lemma:created`
- `sentence:corrected -> lemma:updated`

This is a transition layer. New code should subscribe to canonical event names.
