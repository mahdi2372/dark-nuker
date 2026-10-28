@echo off
title DARK NUKER - Build
cd /d "%~dp0"

echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency install failed.
    pause
    exit /b 1
)

echo Building DARK_NUKER.exe...
pyinstaller --noconfirm --onefile --name DARK_NUKER --icon assets/logo.ico --paths src --collect-all discord --collect-all rich --hidden-import nukebot --hidden-import dotenv --hidden-import keyring run.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo Build complete: dist\DARK_NUKER.exe
pause