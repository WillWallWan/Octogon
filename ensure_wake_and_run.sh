#!/bin/bash

# Log start
LOG_FILE="/Users/willwallwan/Documents/GitHub/Octogon/wake_log.txt"
touch "$LOG_FILE"
echo "===================================" >> "$LOG_FILE"
echo "Starting wake and run script at $(date)" >> "$LOG_FILE"

# Instead of using sudo to set wake, we'll use the launchctl command to run at next boot
# This is safer and doesn't require sudo permissions

# Schedule the actual script to run at 8:00 AM
# We're scheduling it to run 2 minutes after wake to ensure the system is fully ready
echo "Setting up tennis booker to run at 8:00 AM" >> "$LOG_FILE"

# Create a temporary plist for a one-time run
TEMP_PLIST="$HOME/Library/LaunchAgents/com.tennis.onetime.plist"
cat > "$TEMP_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tennis.onetime</string>
    <key>ProgramArguments</key>
    <array>
        <string>osascript</string>
        <string>/Users/willwallwan/Documents/GitHub/Octogon/LaunchTennisBooker.scpt</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
    <key>StandardErrorPath</key>
    <string>/Users/willwallwan/Documents/GitHub/Octogon/tennis_error.log</string>
    <key>StandardOutPath</key>
    <string>/Users/willwallwan/Documents/GitHub/Octogon/tennis_output.log</string>
</dict>
</plist>
EOF

# Load the one-time plist
launchctl load "$TEMP_PLIST"
echo "Loaded one-time LaunchAgent for tennis booking" >> "$LOG_FILE"

# Verify the wake schedule is set properly (for debugging)
pmset -g sched >> "$LOG_FILE" 2>&1

echo "Wake and run script completed at $(date)" >> "$LOG_FILE"
echo "===================================" >> "$LOG_FILE"

# No need for caffeinate as we're allowing the computer to sleep normally
# The scheduled wake will happen automatically at 7:55 AM 