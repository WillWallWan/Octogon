import os
import sys
from datetime import datetime

log_path = "/Users/willwallwan/Documents/GitHub/Octogon/test_launchd_log.txt"

with open(log_path, "a") as f:
    f.write(f"Script started at: {datetime.now()}\n")
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Current working directory: {os.getcwd()}\n")
    f.write("Environment variables:\n")
    for key, value in os.environ.items():
        f.write(f"  {key}: {value}\n")
    f.write("Script finished.\n\n") 