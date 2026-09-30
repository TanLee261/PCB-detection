@echo off
cd /d "%~dp0\.."
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate
pip install -r app\requirements.txt
streamlit run app/app.py
pause
