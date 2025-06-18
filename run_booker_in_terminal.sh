#!/bin/zsh
# This script opens a new Terminal window and runs the tennis booker.
# It ensures the script runs in the foreground, preventing macOS from killing browser processes.

# The full command to run inside the new Terminal window.
# It's broken down for clarity.
# 1. cd: Change to the correct project directory.
# 2. caffeinate: Prevent the Mac from sleeping.
# 3. /.../python3: Use the full path to the Python interpreter in the venv.
# 4. /.../auto_super_tennis_booker.py: The full path to the script.
# 5. The '; read' at the end will keep the window open after the script is done
#    so you can see the output. You'll need to press Enter to close it.

COMMAND_TO_RUN="cd /Users/willwallwan/Octogon; /usr/bin/caffeinate -i /Users/willwallwan/Octogon/venv/bin/python3 /Users/willwallwan/Octogon/auto_super_tennis_booker.py; echo -e '\\nScript finished. Press Enter to close this window.'; read"

# Use osascript to tell the Terminal app to execute our command.
osascript -e "tell application \"Terminal\" to do script \"${COMMAND_TO_RUN}\"" 