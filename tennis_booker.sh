#!/bin/bash

# Keep the computer awake during execution
caffeinate -i &

# Change to the script directory
cd /Users/willwallwan/Documents/GitHub/Octogon

# Activate the virtual environment
source venv/bin/activate

# Run the tennis booker script
python tennis_booker.py

# Deactivate the virtual environment
deactivate

# Kill the caffeinate process
pkill -f caffeinate 