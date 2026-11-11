@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  Lava Shop - setup and run
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python 3.11+ and add to PATH
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  echo [1/4] Creating venv ...
  python -m venv venv
  if errorlevel 1 (
    echo [ERROR] venv failed
    pause
    exit /b 1
  )
) else (
  echo [1/4] venv ok
)

echo [2/4] Installing packages ...
call "venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip failed
  pause
  exit /b 1
)

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Edit .env and set LAVA_API_KEY and LAVA_OFFER_ID
  notepad ".env"
  pause
)

echo [3/4] migrate ...
python manage.py migrate --noinput
if errorlevel 1 (
  echo [ERROR] migrate failed
  pause
  exit /b 1
)

echo [4/4] http://127.0.0.1:8000/
echo Ctrl+C to stop
echo.
python manage.py runserver 127.0.0.1:8000
pause
endlocal
