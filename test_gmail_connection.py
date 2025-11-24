#!/usr/bin/env python3
"""
Test Gmail API connection and authentication
"""
import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """Authenticate and return Gmail service object."""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            print("✓ Loaded existing credentials from token.pickle")
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
            print("✓ Credentials refreshed")
        else:
            print("Starting OAuth flow...")
            print("A browser window will open for authentication.")
            print("Please log in and grant permissions.")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            print("✓ Authentication successful!")
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            print("✓ Credentials saved to token.pickle")
    
    # Build the Gmail service
    service = build('gmail', 'v1', credentials=creds)
    print("✓ Gmail service created")
    
    return service

def test_gmail_access(service):
    """Test basic Gmail access by fetching user profile and recent messages."""
    try:
        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        print(f"\n✓ Connected to Gmail account: {profile['emailAddress']}")
        print(f"  Total messages: {profile['messagesTotal']}")
        print(f"  Total threads: {profile['threadsTotal']}")
        
        # Get recent messages
        print("\nFetching recent messages...")
        results = service.users().messages().list(
            userId='me',
            maxResults=10,
            q='subject:(booking OR reservation OR confirmation)'
        ).execute()
        
        messages = results.get('messages', [])
        print(f"\n✓ Found {len(messages)} recent messages with booking/reservation/confirmation in subject")
        
        if messages:
            print("\nFirst few message subjects:")
            for i, msg in enumerate(messages[:3]):
                # Get message details
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()
                
                # Extract subject
                headers = message['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown sender')
                
                print(f"  {i+1}. {subject[:60]}...")
                print(f"     From: {from_email}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error accessing Gmail: {e}")
        return False

def main():
    print("Gmail API Connection Test")
    print("=" * 50)
    
    # Check for credentials file
    if not os.path.exists('credentials.json'):
        print("✗ Error: credentials.json not found!")
        print("  Please download it from Google Cloud Console")
        return
    
    print("✓ Found credentials.json")
    
    try:
        # Authenticate
        service = authenticate_gmail()
        
        # Test access
        success = test_gmail_access(service)
        
        if success:
            print("\n" + "=" * 50)
            print("✓ Gmail API connection successful!")
            print("You can now use the Gmail reader to fetch booking emails.")
        else:
            print("\n✗ Gmail API test failed")
            
    except Exception as e:
        print(f"\n✗ Error during authentication: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you're using the correct Google account")
        print("2. Check that Gmail API is enabled in Google Cloud Console")
        print("3. Verify the OAuth consent screen is configured")
        print("4. Delete token.pickle and try again if authentication fails")

if __name__ == "__main__":
    main()





