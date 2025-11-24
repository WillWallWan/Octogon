#!/bin/bash
# Setup script for Octogon Tennis Booking System on a new computer

echo "🎾 Octogon Tennis Booking System - New Computer Setup"
echo "======================================================"
echo ""

# Set the project directory
PROJECT_DIR="/Users/willwallwan/Octogon"
cd "$PROJECT_DIR" || exit 1

# Step 1: Check Python version
echo "Step 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Found: $PYTHON_VERSION"
else
    echo "✗ Python 3 not found. Please install Python 3.13 or later."
    exit 1
fi

# Step 2: Create virtual environment
echo ""
echo "Step 2: Setting up Python virtual environment..."
if [ -d "venv" ]; then
    echo "  Virtual environment already exists."
    read -p "  Delete and recreate? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo "✓ Virtual environment recreated"
    fi
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Step 3: Install dependencies
echo ""
echo "Step 3: Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Step 4: Check for Gmail credentials
echo ""
echo "Step 4: Checking Gmail API credentials..."
if [ -f "credentials.json" ]; then
    echo "✓ Found credentials.json"
else
    echo "✗ credentials.json not found"
    echo ""
    echo "  You need to set up Gmail API access:"
    echo "  1. Go to https://console.cloud.google.com/"
    echo "  2. Create a project and enable Gmail API"
    echo "  3. Create OAuth credentials (Desktop app)"
    echo "  4. Download as credentials.json"
    echo "  5. Save to: $PROJECT_DIR/credentials.json"
    echo ""
    echo "  See GMAIL_SETUP.md for detailed instructions"
    echo ""
    read -p "  Press Enter when you've added credentials.json..."
fi

# Step 5: Authenticate with Gmail
echo ""
echo "Step 5: Gmail authentication..."
if [ -f "token.pickle" ]; then
    echo "  Found existing token.pickle"
    read -p "  Re-authenticate? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f token.pickle
        python test_gmail_connection.py
    fi
else
    echo "  Starting Gmail authentication (browser will open)..."
    python test_gmail_connection.py
fi

# Step 6: Test the system
echo ""
echo "Step 6: Testing the result analysis system..."
echo "  Running analysis for today..."
python combine_results.py
if [ $? -eq 0 ]; then
    echo "✓ Result analysis working"
else
    echo "⚠️  Result analysis had issues (this is normal if no bookings today)"
fi

# Step 7: Set up LaunchAgent
echo ""
echo "Step 7: Setting up daily automation (LaunchAgent)..."
PLIST_FILE="$HOME/Library/LaunchAgents/com.willwallwan.autotennisbooker.plist"

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

if [ -f "$PLIST_FILE" ]; then
    echo "  LaunchAgent file already exists"
else
    echo "  Creating LaunchAgent plist file..."
    cat > "$PLIST_FILE" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.willwallwan.autotennisbooker</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/willwallwan/Octogon/run_booker_in_terminal.sh</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>50</integer>
    </dict>

    <key>WorkingDirectory</key>
    <string>/Users/willwallwan/Octogon</string>

    <key>StandardOutPath</key>
    <string>/Users/willwallwan/Octogon/logs/launchd_output.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/willwallwan/Octogon/logs/launchd_error.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>KeepAlive</key>
    <false/>

    <key>AbandonProcessGroup</key>
    <true/>
</dict>
</plist>
EOF
    echo "  ✓ LaunchAgent plist created"
fi

# Unload if already loaded (to refresh)
if launchctl list 2>/dev/null | grep -q com.willwallwan.autotennisbooker; then
    echo "  Unloading existing LaunchAgent..."
    launchctl unload "$PLIST_FILE" 2>/dev/null
fi

# Load the LaunchAgent
echo "  Loading LaunchAgent..."
launchctl load "$PLIST_FILE"

# Verify it's loaded
if launchctl list | grep -q com.willwallwan.autotennisbooker; then
    echo "  ✓ LaunchAgent loaded successfully"
    echo "  Will run daily at 7:50 AM"
else
    echo "  ⚠️  LaunchAgent may not have loaded properly"
    echo "  Try running manually: launchctl load $PLIST_FILE"
fi

# Step 8: Make scripts executable
echo ""
echo "Step 8: Making scripts executable..."
chmod +x run_booker_in_terminal.sh
chmod +x run_daily_workflow.sh
chmod +x run_summary_only.sh
chmod +x setup_new_computer.sh
echo "✓ Scripts are executable"

# Summary
echo ""
echo "======================================================"
echo "✅ Setup Complete!"
echo "======================================================"
echo ""
echo "Next steps:"
echo "1. The booking system will run automatically at 7:50 AM daily"
echo "2. To check booking results, run: python combine_results.py"
echo "3. To manually trigger booking: ./run_booker_in_terminal.sh"
echo ""
echo "Files to check:"
echo "- Booking logs: auto_booker_action.log"
echo "- LaunchAgent logs: logs/launchd_output.log"
echo "- Daily summaries: booking_summary_YYYYMMDD.txt"
echo ""
echo "Documentation:"
echo "- Setup guide: SETUP.md"
echo "- Gmail setup: GMAIL_SETUP.md"
echo "- Tennis rules: rioc_tennis_rules.txt"
echo ""
