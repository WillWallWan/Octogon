#!/bin/bash

# Log file
LOG_FILE="/Users/willwallwan/Documents/GitHub/Octogon/simple_launch_log.txt"
touch "$LOG_FILE"

# Log start time
echo "====================================" >> "$LOG_FILE"
echo "Simple launcher started at $(date)" >> "$LOG_FILE"

# Run the AppleScript directly
osascript /Users/willwallwan/Documents/GitHub/Octogon/LaunchTennisBooker.scpt >> "$LOG_FILE" 2>&1

# Log completion
echo "Simple launcher completed at $(date)" >> "$LOG_FILE"

# Now schedule tomorrow's booking
echo "Scheduling tomorrow's booking..." >> "$LOG_FILE"

# Cancel any existing scheduled jobs (to avoid duplicates)
for job in $(atq | cut -f1); do
  atrm $job
  echo "Removed previous job $job" >> "$LOG_FILE"
done

# Schedule the script to run tomorrow
echo "/bin/bash /Users/willwallwan/Documents/GitHub/Octogon/simple_launch.sh" | at 8:00AM tomorrow

# Log the successful scheduling
echo "Successfully scheduled for tomorrow at 8:00AM" >> "$LOG_FILE"
echo "Current scheduled jobs:" >> "$LOG_FILE"
atq >> "$LOG_FILE"
echo "====================================" >> "$LOG_FILE" 