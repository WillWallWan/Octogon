#!/bin/zsh
# Complete daily workflow: book courts, then generate summary
# This script runs the booking process and then generates a summary after a delay

# Configuration
OCTOGON_DIR="/Users/willwallwan/Octogon"
VENV_PYTHON="$OCTOGON_DIR/venv/bin/python3"
LOG_FILE="$OCTOGON_DIR/daily_workflow.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Change to project directory
cd "$OCTOGON_DIR"

# Start workflow
log_message "Starting daily tennis booking workflow"

# Run the booking script
log_message "Running tennis court booking..."
/usr/bin/caffeinate -i "$VENV_PYTHON" "$OCTOGON_DIR/auto_super_tennis_booker.py" 2>&1 | tee -a "$LOG_FILE"

# Check if booking script completed
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log_message "Booking script completed successfully"
else
    log_message "Booking script failed with exit code ${PIPESTATUS[0]}"
fi

# Wait for emails to arrive (adjust timing as needed)
WAIT_TIME=1800  # 30 minutes
log_message "Waiting $WAIT_TIME seconds for email confirmations..."
sleep $WAIT_TIME

# Generate daily summary
log_message "Generating daily summary..."
"$VENV_PYTHON" "$OCTOGON_DIR/daily_summary_generator.py" 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log_message "Daily summary generated successfully"
else
    log_message "Failed to generate daily summary"
fi

log_message "Daily workflow completed"

# Keep terminal open to see results
echo -e "\nWorkflow finished. Press Enter to close this window."
read





