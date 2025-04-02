#!/bin/bash
cd /Users/willwallwan/Documents/GitHub/Octogon
# Keep computer awake during script execution
caffeinate -i -s -d -m -u -t 300 &
CAFFEINATE_PID=$!

source venv/bin/activate
python tennis_booker.py >> /Users/willwallwan/Documents/GitHub/Octogon/tennis_booker.log 2>&1
deactivate

# Allow computer to sleep again
kill $CAFFEINATE_PID 