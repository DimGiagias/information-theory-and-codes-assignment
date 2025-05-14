#!/bin/bash

# Create a virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install the dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete! Virtual environment is activated."
echo "To activate this environment in the future, run:"
echo "source venv/bin/activate"