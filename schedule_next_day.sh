#!/bin/bash

# Log file
LOG_FILE="/Users/willwallwan/Documents/GitHub/Octogon/scheduler_log.txt"
touch "$LOG_FILE"

# Log start time
echo "====================================" >> "$LOG_FILE"
echo "Scheduler started at $(date)" >> "$LOG_FILE"

# Schedule the simple launcher for 8:00 AM tomorrow
echo "/bin/bash /Users/willwallwan/Documents/GitHub/Octogon/simple_launch.sh" | at 8:00AM tomorrow

# Log the scheduled jobs
echo "Scheduled jobs:" >> "$LOG_FILE"
atq >> "$LOG_FILE"

# Log completion
echo "Scheduler completed at $(date)" >> "$LOG_FILE"
echo "====================================" >> "$LOG_FILE" 