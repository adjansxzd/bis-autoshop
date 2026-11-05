@echo off
REM First-time backend setup on Windows
cd backend
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
echo.
echo Backend ready. Run start_backend.bat
pause
