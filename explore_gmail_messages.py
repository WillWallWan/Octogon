#!/usr/bin/env python3
"""
Explore Gmail messages to understand the format of tennis booking emails
"""
import os
import pickle
import base64
import re
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def get_gmail_service():
    """Get authenticated Gmail service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
    
    return build('gmail', 'v1', credentials=creds)

def get_message_body(payload):
    """Extract body text from email payload."""
    body = ''
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif part['mimeType'] == 'text/html' and not body:
                data = part['body']['data']
                html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                # Simple HTML stripping
                body = re.sub('<[^<]+?>', '', html_body)
    else:
        if payload['body'].get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']).decode('utf-8', errors='ignore')
    
    return body

def explore_recent_emails(service, days_back=7):
    """Explore recent emails to find tennis booking patterns."""
    # Calculate date for search
    after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    
    print(f"Searching emails from the last {days_back} days...")
    print("=" * 70)
    
    # Try different search queries
    search_queries = [
        f'after:{after_date}',  # All recent emails
        f'from:perfectmind after:{after_date}',
        f'from:roosevelt after:{after_date}',
        f'from:rioc after:{after_date}',
        f'subject:tennis after:{after_date}',
        f'subject:court after:{after_date}',
        f'"tennis court" after:{after_date}',
    ]
    
    all_senders = set()
    tennis_related_messages = []
    
    for query in search_queries:
        print(f"\nTrying query: {query}")
        
        try:
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=20
            ).execute()
            
            messages = results.get('messages', [])
            print(f"  Found {len(messages)} messages")
            
            if messages:
                for msg in messages[:5]:  # Check first 5 of each query
                    message = service.users().messages().get(
                        userId='me',
                        id=msg['id']
                    ).execute()
                    
                    # Extract headers
                    headers = message['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                    from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                    
                    all_senders.add(from_email)
                    
                    # Check if tennis/court related
                    if any(word in subject.lower() or word in from_email.lower() 
                          for word in ['tennis', 'court', 'roosevelt', 'rioc', 'perfectmind']):
                        
                        body = get_message_body(message['payload'])
                        
                        tennis_related_messages.append({
                            'id': msg['id'],
                            'subject': subject,
                            'from': from_email,
                            'date': date,
                            'body_preview': body[:500] if body else 'No body'
                        })
                        
        except Exception as e:
            print(f"  Error: {e}")
    
    # Display findings
    print("\n" + "=" * 70)
    print("SUMMARY OF FINDINGS")
    print("=" * 70)
    
    print(f"\nUnique senders found: {len(all_senders)}")
    for i, sender in enumerate(sorted(all_senders)[:10]):
        print(f"  {i+1}. {sender}")
    
    print(f"\nTennis-related messages found: {len(tennis_related_messages)}")
    
    for i, msg in enumerate(tennis_related_messages[:5]):
        print(f"\n--- Message {i+1} ---")
        print(f"From: {msg['from']}")
        print(f"Subject: {msg['subject']}")
        print(f"Date: {msg['date']}")
        print(f"Body preview:")
        print("-" * 50)
        print(msg['body_preview'])
        print("-" * 50)
        
        # Look for patterns
        body_lower = msg['body_preview'].lower()
        if 'court' in body_lower:
            court_matches = re.findall(r'court\s*#?\s*(\d+)', body_lower)
            if court_matches:
                print(f"Courts mentioned: {court_matches}")
        
        # Look for dates
        date_patterns = re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', msg['body_preview'])
        if date_patterns:
            print(f"Dates found: {date_patterns}")
        
        # Look for times
        time_patterns = re.findall(r'\d{1,2}:\d{2}\s*[ap]m', body_lower)
        if time_patterns:
            print(f"Times found: {time_patterns}")

def main():
    print("Gmail Message Explorer - Finding Tennis Booking Emails")
    print("=" * 70)
    
    service = get_gmail_service()
    explore_recent_emails(service, days_back=30)  # Look back 30 days
    
    print("\n\nBased on these findings, we can now create a proper email parser!")
    print("Please share which of these emails are the booking confirmations.")

if __name__ == "__main__":
    main()





