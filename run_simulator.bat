@echo off
setlocal
cd /d "%~dp0"
set "SIMULATOR_PYTHON=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if exist "%SIMULATOR_PYTHON%" (
    "%SIMULATOR_PYTHON%" main.py
) else (
    python main.py
)
if errorlevel 1 pause
