# Corpustar

## Stack

- Backend: FastAPI (host/port from `backend/.env`)
- Frontend: Vite + Electron (host/port from `frontend/.env`)

## Environment

Backend (`backend/.env`):

```dotenv
BACKEND_HOST=127.0.0.1
BACKEND_PORT=619
FRONTEND_ORIGIN=http://127.0.0.1:407
```

Frontend (`frontend/.env`):

```dotenv
FRONTEND_DEV_HOST=127.0.0.1
FRONTEND_DEV_PORT=407
BACKEND_HOST=127.0.0.1
BACKEND_PORT=619
```

## Run

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe run.py
```

Frontend:

```powershell
cd frontend
npm run electron:dev
```

## Notes

- FastAPI CORS allows the frontend origin from `FRONTEND_ORIGIN`.
- Frontend API requests use `VITE_API_BASE_URL` when set, otherwise `BACKEND_HOST` + `BACKEND_PORT`.
- The backend now initializes a SQLite database at `backend/data/corpustar.sqlite3` by default.
- Override the database file with `SQLITE_DATABASE_PATH`.
- If your local sqlite file was created before cascading foreign keys were introduced for
  `documents`/`processings`/`document_sentences`, delete the old DB file and restart backend
  so schema can be recreated with `ON DELETE CASCADE`.
