#!/bin/bash

# Set the working directory
cd /Users/willwallwan/Documents/GitHub/Octogon || exit 1

# Log the execution time and user
echo "Running as user: $(whoami) at $(date)" >> /Users/willwallwan/Documents/GitHub/Octogon/tennis_booker.log

# Keep computer awake during script execution
/usr/bin/caffeinate -i -s -d -m -u -t 300 &
CAFFEINATE_PID=$!

# Activate the virtual environment and run the script
/Users/willwallwan/Documents/GitHub/Octogon/venv/bin/python /Users/willwallwan/Documents/GitHub/Octogon/tennis_booker.py >> /Users/willwallwan/Documents/GitHub/Octogon/tennis_booker.log 2>&1

# Allow computer to sleep again
kill $CAFFEINATE_PID 