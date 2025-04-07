#!/bin/zsh

# Simple wrapper to launch the tennis booking script
# This is intended to be called by a LaunchAgent

# The actual path to the osascript command
OSASCRIPT="/usr/bin/osascript"

# The path to our AppleScript file
APPLESCRIPT="/Users/willwallwan/Documents/GitHub/Octogon/LaunchTennisBooker.scpt"

# Execute the AppleScript
$OSASCRIPT "$APPLESCRIPT" > /Users/willwallwan/Documents/GitHub/Octogon/launch_log.txt 2>&1 