@echo off
cd /d "%~dp0"

echo ===================================================
echo Starting Macro Intelligence Platform Web Interface
echo ===================================================

if not exist "web\frontend\dist\index.html" (
    echo No frontend build found. Building it now...
    cd web\frontend
    call npm install
    call npm run build
    cd ..\..
    echo.
)

echo The web interface will be available at: http://127.0.0.1:8000
echo API documentation will be available at: http://127.0.0.1:8000/docs
echo Press Ctrl+C to stop.
echo.
echo Starting server...

python -m uvicorn web.server:app --host 127.0.0.1 --port 8000
