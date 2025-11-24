# Gmail API Setup Guide

This guide will help you set up Gmail API access for the tennis booking summary system.

## Prerequisites
- A Google account that receives the tennis booking confirmation emails
- Python environment with required packages installed

## Step 1: Enable Gmail API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click on it and press "Enable"

## Step 2: Create OAuth 2.0 Credentials

1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in the required fields (app name, email, etc.)
   - Add your email to test users
   - Add scope: `https://www.googleapis.com/auth/gmail.readonly`

4. Back in Create OAuth client ID:
   - Application type: "Desktop app"
   - Name: "Tennis Booking Summary"
   - Click "Create"

5. Download the credentials:
   - Click the download button (⬇️) next to your OAuth 2.0 Client ID
   - Save the file as `credentials.json` in the Octogon directory

## Step 3: First-Time Authentication

Run the Gmail reader test to authenticate:

```bash
cd /Users/willwallwan/Octogon
source venv/bin/activate
python gmail_reader.py
```

This will:
1. Open a browser window for authentication
2. Ask you to log in and grant permissions
3. Create a `token.pickle` file for future use

## Step 4: Set Up LLM API Key

Choose either OpenAI or Anthropic:

### For OpenAI:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### For Anthropic:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Add this to your `.zshrc` or `.bash_profile` to make it permanent.

## Step 5: Test the System

Run a test summary generation:

```bash
python daily_summary_generator.py --date 2025-09-05
```

## Troubleshooting

### "Credentials file not found"
Make sure `credentials.json` is in the Octogon directory.

### "Token has been expired or revoked"
Delete `token.pickle` and run the authentication process again.

### Gmail not finding emails
1. Check that booking confirmation emails are in your inbox
2. Verify the sender email address in `gmail_reader.py`
3. Try increasing `days_back` parameter

### No LLM API key
The system will fall back to a basic summary without AI enhancement. Set the appropriate environment variable to enable AI summaries.

## Security Notes

- Keep `credentials.json` and `token.pickle` secure and don't commit them to git
- Add both files to `.gitignore`
- The Gmail API access is read-only for security





