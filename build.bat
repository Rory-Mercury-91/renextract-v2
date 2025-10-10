@echo off
echo ================================================
echo BUILD EXECUTABLE - PyWebView + Svelte
echo ================================================

REM Check that Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Install Python from https://python.org
    pause
    exit /b 1
)

REM Install dependencies if necessary
echo Installing dependencies...
pip install -r requirements.txt

REM Build frontend if necessary
if not exist "dist\index.html" (
    echo Building frontend...
    python run.py --build-only
)

REM Build executable
echo Building executable...
python build_exe.py

REM Clean frontend artifacts copied into the executable
if exist "dist\index.html" del /Q "dist\index.html"
if exist "dist\favicon.ico" del /Q "dist\favicon.ico"
if exist "dist\assets" rmdir /S /Q "dist\assets"

echo.
echo ================================================
echo BUILD COMPLETED!
echo ================================================
echo Executable: dist\app.exe
echo.
pause
