# Corpustar

## Intro

Corpustar is not a general-purpose linguistic NLP tool.

It is focused on one concrete workflow:

1. Import documents.
2. Split the text into sentences.
3. Review and correct sentence boundaries.
4. Lemmatize the text.
5. Load `funktionsverbgefuege.csv`.
6. Produce FVG statistics for the text.

The project is built for linguistic researchers who often have to spread one workflow across several tools and then count results manually. That workflow is slow, fragmented, and difficult to audit. When one black-box step fails, the final result becomes hard to trace back to its source.

Corpustar aims to make each step traceable. The goal is a simple UI and user-friendly UX that help linguists work with long texts and still obtain transparent statistical results. 

The desktop app is designed around a human-in-the-loop workflow: human experts can add rules to the database, save time in later processing, and improve the system further through text annotation and rule refinement.

Another design goal is modest resource usage. The software is intended to run on ordinary computers without demanding heavy infrastructure.

## Get Started

### What runs in this project

During development, you usually run two parts:

- A Python backend in `backend/`
- An Electron + Vite frontend in `frontend/`

Default local ports:

- Backend: `127.0.0.1:619`
- Frontend dev server: `127.0.0.1:407`

### Windows

Backend:

```powershell
cd D:\projects\Corpustar\backend
.\.venv\Scripts\Activate.ps1
python run.py
```

Frontend desktop app:

```powershell
cd D:\projects\Corpustar\frontend
npm install
npm run electron:dev
```

### Linux

Backend:

```bash
cd /path/to/Corpustar/backend
source .venv/bin/activate
python run.py
```

Frontend desktop app:

```bash
cd /path/to/Corpustar/frontend
npm install
npm run electron:dev
```

### macOS

Backend:

```bash
cd /path/to/Corpustar/backend
source .venv/bin/activate
python run.py
```

Frontend desktop app:

```bash
cd /path/to/Corpustar/frontend
npm install
npm run electron:dev
```

## Troubleshooting

### Check whether a port is already in use

Replace `<PORT>` with the port you want to inspect, for example `619`.

Windows:

```powershell
netstat -ano | findstr :<PORT>
```

Linux:

```bash
ss -ltnp | grep :<PORT>
```

Alternative on Linux:

```bash
lsof -i :<PORT>
```

macOS:

```bash
lsof -i :<PORT>
```

### Free an occupied port

#### Windows

Find the PID:

```powershell
netstat -ano | findstr :619
```

Stop the process:

```powershell
Stop-Process -Id <PID> -Force
```

Alternative:

```powershell
taskkill /PID <PID> /F
```

#### Linux

Find the PID:

```bash
lsof -i :619
```

Stop the process:

```bash
kill <PID>
```

If it does not stop:

```bash
kill -9 <PID>
```

#### macOS

Find the PID:

```bash
lsof -i :619
```

Stop the process:

```bash
kill <PID>
```

If it does not stop:

```bash
kill -9 <PID>
```

### Common startup issue

If you see a message like `port 619 is already in use`, another backend instance is still running or did not shut down cleanly. Stop that process first, then start the backend again.

If you see `ModuleNotFoundError: No module named 'app'`, you started the backend from the wrong directory. Change into `backend/` first and then run:

```bash
python run.py
```
