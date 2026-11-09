@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    start "" ".venv\Scripts\python.exe" run.py
) else (
    echo Virtual environment not found. Please run: uv venv --python 3.11 ^&^& uv pip install -r requirements.txt
    pause
)
