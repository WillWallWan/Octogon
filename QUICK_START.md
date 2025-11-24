# Octogon Tennis Booking - Quick Start Guide

## 🎾 What This System Does

**Automated Tennis Court Booking System** for Roosevelt Island courts that:
1. **Books courts automatically** every morning at 7:50 AM
2. **Tracks booking results** via Gmail integration  
3. **Analyzes performance** with detailed timing metrics
4. **Recommends optimizations** to improve success rate

---

## ⚡ Quick Setup (New Computer)

```bash
cd /Users/willwallwan/Octogon
chmod +x setup_new_computer.sh
./setup_new_computer.sh
```

This automated script will:
- Set up Python virtual environment
- Install all dependencies
- Guide you through Gmail API authentication
- Configure daily automation

---

## 📊 Daily Usage

### Check Today's Booking Results
```bash
cd /Users/willwallwan/Octogon
source venv/bin/activate
python combine_results.py
```

### Check Specific Date
```bash
python combine_results.py --date 2025-11-20
```

### What You'll See:
- ✅ Which bookings succeeded
- ❌ Which failed (too early/too late)
- 🚫 Technical failures
- ❓ Pending results
- 🎯 Timing sweet spot analysis
- 💡 Recommendations for improvement

---

## 🔧 System Components

### Core Scripts:
- **`auto_super_tennis_booker.py`** - Main booking automation
- **`combine_results.py`** - Results analyzer (logs + emails)
- **`config.py`** - User credentials & court priorities

### Supporting Scripts:
- **`gmail_reader.py`** - Gmail API integration
- **`parse_booking_attempts.py`** - Log parser
- **`test_gmail_connection.py`** - Gmail auth tester

### Automation:
- **`run_booker_in_terminal.sh`** - Launcher for booking script
- **LaunchAgent plist** - Schedules daily 7:50 AM execution

---

## 📁 Important Files

### Configuration:
- `config.py` - 12 user accounts, court priorities, timing rules

### Credentials (keep secure, don't commit):
- `credentials.json` - Gmail API credentials
- `token.pickle` - Gmail authentication token

### Logs:
- `auto_booker_action.log` - All booking attempts with timestamps
- `logs/launchd_output.log` - LaunchAgent output
- `logs/launchd_error.log` - LaunchAgent errors

### Generated Reports:
- `booking_summary_YYYYMMDD.txt` - Daily analysis reports

---

## 🎯 Court Booking Strategy

Current priority order (from `config.py`):
```
Priority 1-2:   Court 6 at 6 PM & 7 PM
Priority 3-4:   Court 5 at 6 PM & 7 PM  
Priority 5-6:   Court 3 at 6 PM & 7 PM
Priority 7-8:   Court 2 at 6 PM & 7 PM
```

Each priority uses 2 accounts for redundancy.

---

## 📅 Booking Rules (RIOC)

- Bookings open at **8:00 AM** on weekdays
- Can book **2 days in advance**
- Friday books for **Monday + Tuesday** (3-4 days)
- One booking per account per day
- Booking window: 8 AM - 4 PM weekdays

---

## 🔍 Troubleshooting

### Gmail token expired
```bash
rm -f token.pickle
python test_gmail_connection.py
```

### LaunchAgent not running
```bash
launchctl unload ~/Library/LaunchAgents/com.willwallwan.autotennisbooker.plist
launchctl load ~/Library/LaunchAgents/com.willwallwan.autotennisbooker.plist
launchctl list | grep tennis
```

### Check if booking ran today
```bash
tail -50 auto_booker_action.log | grep "Script started"
```

### View LaunchAgent logs
```bash
tail logs/launchd_output.log
tail logs/launchd_error.log
```

---

## 📈 Understanding Results

### Email Result Categories:
1. **"Your Tennis Permit has been approved"** = ✅ Success
2. **"Unable to Process your request"** = ❌ Too late (courts taken)
3. **"Your permit request has been canceled"** = ❌ Too early (server not ready)
4. **"Pending Approval"** = Submission confirmation
5. **No email** = 🚫 Technical failure

### Timing Analysis:
The system tracks exact submission timestamps (to the millisecond) and identifies:
- When submissions are "too early" (cancelled)
- When submissions are "too late" (rejected)
- The "sweet spot" timing window (if one exists)

---

## 🚀 Advanced Usage

### Analyze historical patterns
```bash
# Check last week
for date in 2025-11-{14..20}; do
    python combine_results.py --date $date
done
```

### Manual booking trigger
```bash
./run_booker_in_terminal.sh
```

### Run just the summary
```bash
./run_summary_only.sh
```

---

## 📞 Support Files

- **SETUP.md** - Detailed setup instructions
- **GMAIL_SETUP.md** - Gmail API configuration guide
- **rioc_tennis_rules.txt** - Official tennis court rules
- **README.md** - Project overview


