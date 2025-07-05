@echo off
REM Check if virtual environment exists
IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing requirements...
    pip install requests beautifulsoup4 PyQt5 tqdm
) ELSE (
    call venv\Scripts\activate.bat
)

REM Run the application
python downloader_gui.py
pause
