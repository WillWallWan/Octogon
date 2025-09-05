#!/bin/zsh

# Log the execution time and user
echo "Running as user: $(whoami) at $(date)" >> "/Users/willwallwan/Documents/GitHub/Octogon/tennis_booker.log"

# Set the working directory
cd "/Users/willwallwan/Documents/GitHub/Octogon" || exit 1

# Keep computer awake during script execution
/usr/bin/caffeinate -i -s -d -m -u -t 300 &
CAFFEINATE_PID=$!

# Activate the virtual environment and run the script with absolute paths
"/Users/willwallwan/Documents/GitHub/Octogon/venv/bin/python" "/Users/willwallwan/Documents/GitHub/Octogon/tennis_booker.py" >> "/Users/willwallwan/Documents/GitHub/Octogon/tennis_booker.log" 2>&1

# Allow computer to sleep again
kill $CAFFEINATE_PID

# Signal success
echo "Script completed at $(date)" >> "/Users/willwallwan/Documents/GitHub/Octogon/tennis_booker.log" 