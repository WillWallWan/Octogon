#!/usr/bin/env python3
"""
Analyze tennis booking emails by checking subject lines
"""
import os
import pickle
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from collections import defaultdict

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

def analyze_booking_emails(service, days_back=1):
    """Analyze booking emails from Civic Permits."""
    # Calculate date for search
    after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    
    print(f"Analyzing booking emails from the last {days_back} day(s)...")
    print("=" * 60)
    
    # Search for Civic Permits emails
    query = f'from:donotreply@notify.civicpermits.com after:{after_date}'
    
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=100
        ).execute()
        
        messages = results.get('messages', [])
        print(f"Found {len(messages)} emails from Civic Permits\n")
        
        # Categorize emails
        approved = []
        rejected = []
        canceled = []
        other = []
        
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id']
            ).execute()
            
            # Extract headers
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Parse datetime
            try:
                # Convert email date to datetime
                from email.utils import parsedate_to_datetime
                email_datetime = parsedate_to_datetime(date)
                email_time = email_datetime.strftime('%Y-%m-%d %H:%M:%S')
            except:
                email_time = date
            
            email_info = {
                'subject': subject,
                'time': email_time,
                'id': msg['id']
            }
            
            # Categorize by subject
            if "Your Tennis Permit has been approved" in subject:
                approved.append(email_info)
            elif "Unable to Process your request" in subject:
                rejected.append(email_info)
            elif "Your permit request has been canceled" in subject:
                canceled.append(email_info)
            else:
                other.append(email_info)
        
        # Display results
        print(f"✅ APPROVED BOOKINGS: {len(approved)}")
        print("-" * 60)
        for email in sorted(approved, key=lambda x: x['time']):
            print(f"  {email['time']} - {email['subject']}")
        
        print(f"\n❌ REJECTED BOOKINGS (Unable to Process): {len(rejected)}")
        print("-" * 60)
        for email in sorted(rejected, key=lambda x: x['time']):
            print(f"  {email['time']} - {email['subject']}")
        
        print(f"\n🚫 CANCELED BOOKINGS: {len(canceled)}")
        print("-" * 60)
        for email in sorted(canceled, key=lambda x: x['time']):
            print(f"  {email['time']} - {email['subject']}")
        
        if other:
            print(f"\n❓ OTHER EMAILS: {len(other)}")
            print("-" * 60)
            for email in sorted(other, key=lambda x: x['time']):
                print(f"  {email['time']} - {email['subject']}")
        
        # Summary
        total = len(approved) + len(rejected) + len(canceled)
        success_rate = (len(approved) / total * 100) if total > 0 else 0
        
        if total > 0:
            print(f"\n📊 SUMMARY")
            print("-" * 60)
            print(f"Total booking attempts: {total}")
            print(f"  Approved: {len(approved)}")
            print(f"  Rejected (Unable to Process): {len(rejected)}")
            print(f"  Canceled: {len(canceled)}")
            print(f"Success rate: {success_rate:.1f}% ({len(approved)}/{total})")
        
        return {
            'approved': approved,
            'rejected': rejected,
            'canceled': canceled,
            'other': other,
            'total_attempts': total,
            'success_count': len(approved),
            'rejected_count': len(rejected),
            'canceled_count': len(canceled),
            'success_rate': success_rate
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("Tennis Booking Email Analysis")
    print("=" * 60)
    
    service = get_gmail_service()
    
    # Analyze today's bookings
    print("\nToday's bookings:")
    analyze_booking_emails(service, days_back=1)
    
    # Analyze this week's bookings
    print("\n\nThis week's bookings:")
    analyze_booking_emails(service, days_back=7)

if __name__ == "__main__":
    main()
