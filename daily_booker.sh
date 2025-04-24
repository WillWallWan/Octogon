#!/bin/bash

# Log file
LOG_FILE="/Users/willwallwan/Documents/GitHub/Octogon/daily_booking_log.txt"
touch "$LOG_FILE"

# Log start time
echo "===================================" >> "$LOG_FILE"
echo "Daily booking script started at $(date)" >> "$LOG_FILE"

# Go to the proper directory
cd /Users/willwallwan/Documents/GitHub/Octogon

# Run the tennis booking script
echo "Running tennis booking script..." >> "$LOG_FILE"
python3 tennis_booker.py >> "$LOG_FILE" 2>&1

# Schedule for tomorrow
echo "Scheduling for tomorrow..." >> "$LOG_FILE"

# Remove existing scheduled jobs
for job in $(atq | cut -f1); do
  atrm $job
  echo "Removed previous job $job" >> "$LOG_FILE"
done

# Schedule this script to run tomorrow at 8:00 AM
echo "/bin/bash /Users/willwallwan/Documents/GitHub/Octogon/daily_booker.sh" | at 8:00AM tomorrow

# Log the scheduled jobs
echo "Current scheduled jobs:" >> "$LOG_FILE"
atq >> "$LOG_FILE"

# Log completion
echo "Daily booking script completed at $(date)" >> "$LOG_FILE"
echo "===================================" >> "$LOG_FILE" 