# Octogon Tennis Booking System - Setup Guide

Complete setup instructions for a new computer.

## Prerequisites
- macOS (for LaunchAgent automation)
- Python 3.13
- Google Chrome browser
- Git (to clone/pull the repository)

---

## Step 1: Python Environment Setup

```bash
cd /Users/willwallwan/Octogon

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Gmail API Setup (for result tracking)

### 2.1 Enable Gmail API in Google Cloud Console

1. Go to https://console.cloud.google.com/
2. Create/select project "Tennis Booking Reader"
3. Enable Gmail API:
   - APIs & Services → Library
   - Search "Gmail API" → Enable

### 2.2 Create OAuth Credentials

1. APIs & Services → Credentials
2. Configure OAuth Consent Screen (if needed):
   - External user type
   - App name: "Tennis Booking Summary"
   - Add scope: `https://www.googleapis.com/auth/gmail.readonly`
   - Add your email as test user
3. Create OAuth client ID:
   - Application type: "Desktop app"
   - Download credentials as `credentials.json`
   - Save to `/Users/willwallwan/Octogon/credentials.json`

### 2.3 Authenticate

```bash
cd /Users/willwallwan/Octogon
source venv/bin/activate
python test_gmail_connection.py
```

This opens a browser for you to log in. After authentication, a `token.pickle` file will be created.

---

## Step 3: Test the Booking System

### Test booking script (without actually booking):
```bash
source venv/bin/activate
# Review the config first
cat config.py

# The booking script would run automatically, but you can test manually
# (Comment out actual booking code if you want to test without booking)
```

### Test result analysis:
```bash
source venv/bin/activate
python combine_results.py --date 2025-11-07
```

---

## Step 4: Set Up Daily Automation

### 4.1 Update LaunchAgent file path

The LaunchAgent file is at:
```
/Users/willwallwan/Library/LaunchAgents/com.willwallwan.autotennisbooker.plist
```

Verify the paths in the plist file are correct:
```xml
<string>/Users/willwallwan/Octogon/run_booker_in_terminal.sh</string>
<string>/Users/willwallwan/Octogon</string>
```

### 4.2 Load the LaunchAgent

```bash
# Unload if already loaded
launchctl unload ~/Library/LaunchAgents/com.willwallwan.autotennisbooker.plist 2>/dev/null

# Load the agent
launchctl load ~/Library/LaunchAgents/com.willwallwan.autotennisbooker.plist

# Verify it's loaded
launchctl list | grep tennis
```

The system will now run automatically at 7:50 AM every day.

---

## Step 5: Verify Everything Works

### Check logs:
```bash
# View recent booking attempts
tail -100 auto_booker_action.log

# View LaunchAgent logs
tail -20 logs/launchd_output.log
tail -20 logs/launchd_error.log
```

### Run a manual analysis:
```bash
source venv/bin/activate
python combine_results.py
```

---

## File Structure

```
/Users/willwallwan/Octogon/
├── auto_super_tennis_booker.py    # Main booking script
├── config.py                       # User credentials & priorities
├── combine_results.py              # Daily summary generator
├── gmail_reader.py                 # Gmail API integration
├── parse_booking_attempts.py       # Log parser
├── test_gmail_connection.py        # Gmail auth test
├── run_booker_in_terminal.sh       # Launcher script
├── credentials.json                # Gmail API credentials (you provide)
├── token.pickle                    # Gmail auth token (auto-generated)
├── venv/                           # Python virtual environment
├── logs/                           # LaunchAgent logs
├── auto_booker_action.log          # Booking attempt logs
└── requirements.txt                # Python dependencies
```

---

## Daily Workflow

1. **7:50 AM** - LaunchAgent runs booking script
2. **~8:00 AM** - Bookings are submitted
3. **~8:30 AM** - Email results arrive
4. **Anytime after** - Run `python combine_results.py` to see summary

---

## Common Commands

```bash
# Activate virtual environment (required for all Python commands)
source venv/bin/activate

# Check today's results
python combine_results.py

# Check specific date
python combine_results.py --date 2025-11-20

# Test Gmail connection
python test_gmail_connection.py

# View recent bookings in logs
tail -100 auto_booker_action.log

# Check LaunchAgent status
launchctl list | grep tennis
```

---

## Troubleshooting

### Gmail authentication expired
```bash
rm -f token.pickle
python test_gmail_connection.py
```

### Update Python dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### Check if LaunchAgent is running
```bash
launchctl list | grep com.willwallwan.autotennisbooker
```

### Manually trigger a booking (for testing)
```bash
./run_booker_in_terminal.sh
```

---

## Security Notes

**Don't commit to git:**
- `credentials.json` (Gmail API credentials)
- `token.pickle` (Gmail auth token)
- `.env` files with API keys

These are already in `.gitignore`.


