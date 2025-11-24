# Octogon - Automated Tennis Court Booking System

An intelligent automation system for booking tennis courts on Roosevelt Island, NYC with Gmail integration and AI-powered result tracking.

## 🎾 Features

### Automated Court Booking
- Runs daily at 7:50 AM via macOS LaunchAgent
- Books courts 2 days in advance (following RIOC rules)
- Uses 12 accounts to maximize booking success
- Prioritizes preferred courts (5 & 6) and times (6-8 PM)
- Submits in parallel for maximum speed

### Email Result Tracking
- Integrates with Gmail API to read booking confirmations
- Tracks approved, rejected, and cancelled bookings
- Identifies which accounts succeeded or failed
- Provides 100% visibility into booking outcomes

### Performance Analysis
- Parses logs to extract all booking attempts with timestamps
- Matches log attempts with email results
- Generates comprehensive daily summaries
- Tracks success rates by court, time, and account
- Identifies timing patterns (too early vs too late)
- Calculates the "sweet spot" for optimal submission timing

### Historical Analysis
- Analyze any past booking session by date
- Compare performance across days
- Identify trends and patterns
- Data-driven optimization recommendations

## 🚀 Quick Start (New Computer)

```bash
cd /Users/willwallwan/Octogon
./setup_new_computer.sh
```

See **QUICK_START.md** and **SETUP.md** for detailed instructions.

## 📊 Check Booking Results

```bash
# Activate virtual environment
source venv/bin/activate

# Check today's results
python combine_results.py

# Check specific date
python combine_results.py --date 2025-11-20
```

## 📁 Key Files

- **`auto_super_tennis_booker.py`** - Main booking automation
- **`combine_results.py`** - Daily summary generator
- **`config.py`** - User credentials & court priorities
- **`gmail_reader.py`** - Gmail API integration
- **`parse_booking_attempts.py`** - Log parser

## 📈 What You Get

**Daily Summary Shows:**
- Overall success rate and statistics
- Submission order with exact timestamps
- Account performance breakdown
- Court and time slot success rates
- Email tracking analysis (confirmations vs decisions)
- Timing sweet spot analysis
- Actionable recommendations

## 🎯 Current Strategy

- **Priority courts**: 6, 5, 3, 2 (in that order)
- **Priority times**: 6 PM, 7 PM, 8 PM
- **Accounts**: 12 different accounts for redundancy
- **Timing**: Submits at 8:00:00 + configurable offset
- **Submission**: Parallel execution across all accounts

## 🔒 Security

Files excluded from git (in `.gitignore`):
- `credentials.json` - Gmail API credentials
- `token.pickle` - Gmail auth token
- Logs and screenshots
- Virtual environment

## 📖 Documentation

- **SETUP.md** - Complete setup guide
- **QUICK_START.md** - Quick reference
- **GMAIL_SETUP.md** - Gmail API configuration
- **rioc_tennis_rules.txt** - Official court rules

## 🛠️ Troubleshooting

See **SETUP.md** for common issues and solutions.