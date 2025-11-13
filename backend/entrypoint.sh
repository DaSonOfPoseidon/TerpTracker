#!/bin/bash

# Set DISPLAY environment variable
export DISPLAY=:99

# Check if Xvfb is already running
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "Starting Xvfb on display :99..."
    # Remove stale lock file if it exists
    rm -f /tmp/.X99-lock
    # Start Xvfb
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    # Wait for Xvfb to start
    sleep 2
    echo "Xvfb started"
else
    echo "Xvfb is already running"
fi

# Initialize strain database with public datasets (runs only on first launch)
echo "Checking dataset initialization..."
python -m app.data.init_datasets

# Start uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
