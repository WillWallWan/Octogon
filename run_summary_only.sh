#!/bin/zsh
# Run only the summary generation (useful for testing or running separately)

OCTOGON_DIR="/Users/willwallwan/Octogon"
VENV_PYTHON="$OCTOGON_DIR/venv/bin/python3"

cd "$OCTOGON_DIR"

# Activate virtual environment and run summary generator
source venv/bin/activate

# Run with current date by default, or pass a specific date
if [ $# -eq 0 ]; then
    python daily_summary_generator.py
else
    python daily_summary_generator.py --date "$1"
fi





