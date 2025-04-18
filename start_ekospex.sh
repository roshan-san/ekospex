#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export PYTHONUNBUFFERED=1

# Run the application
python eko.py

# If the application exits, restart it
while true; do
    echo "Ekospex has exited. Restarting in 5 seconds..."
    sleep 5
    python eko.py
done 