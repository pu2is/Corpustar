# Windows Install and Troubleshooting Notes (Corpustar)

Date: 2026-04-07

This file summarizes what you asked during setup and the fixes that worked.

## 1. Clone Repo to Local Folder

You asked how to pull `github.com/pu2is/Corpustar` into your folder.

Commands used:

```powershell
cd E:\corpustar
git clone https://github.com/pu2is/Corpustar.git .
```

If folder is not empty, clone without `.` so Git creates a subfolder:

```powershell
git clone https://github.com/pu2is/Corpustar.git
```

## 2. Backend Python .venv Setup (Windows)

You asked how to set up Python virtual env for backend.

Commands:

```powershell
cd E:\corpustar\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
if (Test-Path .\requirements.txt) { pip install -r .\requirements.txt }
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 3. Frontend Node.js/npm/Electron Setup

You asked how to install Node.js and frontend dependencies.

Normal flow:

```powershell
cd E:\corpustar\frontend
npm install
npm install --save-dev electron
```

## 4. winget Admin Error and Wrong Command

Problem you saw:
- `winget source reset --force` required admin rights.
- `Start-PcsvDevice powershell -Verb RunAs` was the wrong command.

Correct command:

```powershell
Start-Process powershell -Verb RunAs
```

Then in elevated shell:

```powershell
winget source reset --force
winget source update
winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
```

## 5. Node Installed but npm Broken

Problem you saw:
- `node -v` worked.
- `npm -v` failed: missing module under `node_modules\npm\bin\npm-prefix.js`.

Cause:
- Incomplete Node folder from temp extraction.

Fix that worked:
- Install a complete Node zip (user-level), then update PATH.
- Final verification succeeded:
  - `node -v` -> `v22.16.0`
  - `npm -v` -> `10.9.2`
  - `npx -v` -> `10.9.2`

## 6. VS Code Terminal Could Not Find npm

Problem you saw:
- External PowerShell had npm.
- VS Code terminal said npm not recognized.

Cause:
- VS Code terminal had stale PATH.

Fix:
- Fully close and reopen VS Code.
- Or reload PATH in terminal:

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

## 7. npm install Failed (EPERM / electron)

Problem you saw:
- `EPERM rmdir` cleanup failure.
- Electron install step failed/interrupted (`^C`).

Fix approach:

```powershell
cd E:\corpustar\frontend
taskkill /F /IM node.exe /T
taskkill /F /IM Code.exe /T
taskkill /F /IM electron.exe /T
Remove-Item -Recurse -Force .\node_modules -ErrorAction SilentlyContinue
Remove-Item -Force .\package-lock.json -ErrorAction SilentlyContinue
npm cache clean --force
npm install --verbose
```

This eventually succeeded in your terminal (`npm install --verbose` exit code 0).

## 8. spaCy German Model Requirement (Backend Lemmatize)

You asked whether German model auto-downloads.

Answer:
- It does NOT auto-download in code.
- `backend/app/core/process/lemmatize.py` tries:
  - `de_core_news_md`
  - fallback `de_core_news_sm`
- If missing, it raises RuntimeError.

Install commands (inside backend venv):

```powershell
cd E:\corpustar\backend
.\.venv\Scripts\Activate.ps1
pip install -U spacy
python -m spacy download de_core_news_md
python -m spacy download de_core_news_sm
python -m spacy validate
```

## 9. Current Status Summary

Working items confirmed by your outputs:
- Node is installed and usable.
- npm and npx are usable.
- Frontend `npm install --verbose` completed successfully.
- Backend venv activation command ran successfully.

Recommended next run commands:

```powershell
# backend
cd E:\corpustar\backend
.\.venv\Scripts\Activate.ps1
python -m spacy validate

# frontend
cd E:\corpustar\frontend
npm run dev
```
