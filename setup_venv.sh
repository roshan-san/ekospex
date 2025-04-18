#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

echo "Setting up Ekospex virtual environment..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "ven" ]; then
    echo "Creating virtual environment 'ven'..."
    python3 -m venv ven
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please check your Python installation."
        exit 1
    fi
else
    echo "Virtual environment 'ven' already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source ven/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    echo "GOOGLE_API_KEY=\"your_api_key_here\"" > .env
    echo "Please edit the .env file to add your Google API key."
fi

echo "Setup complete!"
echo "To activate the virtual environment, run: source ven/bin/activate"
echo "To run Ekospex, make sure the virtual environment is activated and run: python eko.py" 