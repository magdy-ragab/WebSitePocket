#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing requirements..."
    pip install requests beautifulsoup4 PyQt5 tqdm
else
    source venv/bin/activate
fi

# Run the application
python downloader_gui.py
