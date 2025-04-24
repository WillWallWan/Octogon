#!/bin/bash

# Log start
echo "Manually setting wake up for tomorrow at $(date)" >> "/Users/willwallwan/Documents/GitHub/Octogon/wake_log.txt"

# Clear any existing wake schedule
sudo pmset repeat cancel

# Get tomorrow's date in the format MM/DD/YY
TOMORROW=$(date -v+1d "+%m/%d/%y")

# Set wake time for tomorrow at 7:58 AM
sudo pmset schedule wake "$TOMORROW 07:58:00"

# Log the scheduled wake time
echo "Scheduled one-time wake for $TOMORROW at 07:58:00" >> "/Users/willwallwan/Documents/GitHub/Octogon/wake_log.txt"

# Display confirmation to user
echo "Wake-up scheduled for tomorrow ($TOMORROW) at 7:58 AM"
echo "The tennis booking script will run at 8:00 AM" 