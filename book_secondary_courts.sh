#!/bin/bash
cd /Users/willwallwan/Documents/GitHub/Octogon
# Keep computer awake during script execution
caffeinate -i -s -d -m -u -t 300 &
CAFFEINATE_PID=$!

source venv/bin/activate
python manual_tennis_booker.py
deactivate

# Allow computer to sleep again
kill $CAFFEINATE_PID 