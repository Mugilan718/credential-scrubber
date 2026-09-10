#!/bin/bash
echo "Installing dependencies (first run only)..."
python3 -m pip install -r requirements.txt --quiet
echo "Starting Credential Scrubber..."
python3 app.py
