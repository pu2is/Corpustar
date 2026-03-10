# Corpustar

## Stack

- Backend: FastAPI on `127.0.0.1:619`
- Frontend: Vite + Electron on `127.0.0.1:407`

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

- FastAPI CORS allows the frontend origin at `http://127.0.0.1:407`.
- The Vue app checks `http://127.0.0.1:619/api/health` on startup.
- Override the frontend API target with `VITE_API_BASE_URL` if needed.
- The backend now initializes a SQLite database at `backend/data/corpustar.sqlite3` by default.
- Override the database file with `SQLITE_DATABASE_PATH`.
