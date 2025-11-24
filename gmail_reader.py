"""
Gmail integration for reading tennis court booking confirmation emails.
"""
import os
import re
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

logger = logging.getLogger(__name__)


class GmailReader:
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        """Initialize Gmail API client."""
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._get_gmail_service()
    
    def _get_gmail_service(self):
        """Authenticate and return Gmail service object."""
        creds = None
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('gmail', 'v1', credentials=creds)
    
    def get_booking_emails(self, days_back=1) -> List[Dict]:
        """
        Fetch tennis booking confirmation emails from the last N days.
        
        Args:
            days_back: Number of days to look back for emails
            
        Returns:
            List of email dictionaries with parsed booking information
        """
        try:
            # Calculate the date range
            after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            
            # Search query for RIOC booking emails - both confirmation and decision emails
            # Adjust the from address based on actual sender
            query = f'from:noreply@perfectmind.com OR from:roosevelt@perfectmind.com after:{after_date} (subject:"booking" OR subject:"reservation" OR subject:"confirmation" OR subject:"pending approval" OR subject:"application has been received")'
            
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            
            booking_emails = []
            for message in messages:
                email_data = self._parse_booking_email(message['id'])
                if email_data:
                    booking_emails.append(email_data)
            
            return booking_emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _parse_booking_email(self, message_id: str) -> Optional[Dict]:
        """Parse a single email to extract booking information."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()
            
            # Extract email metadata
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Get email body
            body = self._get_email_body(message['payload'])
            
            # Parse booking details from body
            booking_info = self._extract_booking_details(body, subject)
            
            if booking_info:
                booking_info.update({
                    'email_id': message_id,
                    'subject': subject,
                    'from': from_email,
                    'date_received': date_str,
                    'raw_body': body[:500]  # Store first 500 chars for debugging
                })
                
                return booking_info
                
        except Exception as e:
            logger.error(f"Error parsing email {message_id}: {e}")
            
        return None
    
    def _get_email_body(self, payload) -> str:
        """Extract body text from email payload."""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html':
                    # Fall back to HTML if no plain text
                    if not body:
                        data = part['body']['data']
                        html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # Simple HTML stripping (could be improved with BeautifulSoup)
                        body = re.sub('<[^<]+?>', '', html_body)
        else:
            # Simple message
            if payload['body'].get('data'):
                body = base64.urlsafe_b64decode(
                    payload['body']['data']).decode('utf-8', errors='ignore')
        
        return body
    
    def _extract_booking_details(self, body: str, subject: str) -> Optional[Dict]:
        """
        Extract booking details from email body.
        This needs to be customized based on actual email format.
        """
        booking_info = {}
        
        # Determine email type and status
        body_lower = body.lower()
        subject_lower = subject.lower()
        
        # Check for submission confirmation emails first
        if ('pending approval' in subject_lower or 
            'application has been received' in subject_lower or
            'your application has been received' in body_lower or
            'pending approval' in body_lower):
            booking_info['email_type'] = 'submission_confirmation'
            booking_info['status'] = 'pending'
        # Check for final decision emails
        elif 'confirmed' in body_lower or ('confirmation' in body_lower and 'approved' in body_lower):
            booking_info['email_type'] = 'final_decision'
            booking_info['status'] = 'approved'
        elif ('cancelled' in body_lower or 'declined' in body_lower or 'unavailable' in body_lower or
              'denied' in body_lower or 'rejected' in body_lower):
            booking_info['email_type'] = 'final_decision'
            booking_info['status'] = 'rejected'
        else:
            # Try to determine from subject for legacy emails
            if 'confirmation' in subject_lower:
                booking_info['email_type'] = 'final_decision'
                booking_info['status'] = 'approved'
            else:
                booking_info['email_type'] = 'unknown'
                booking_info['status'] = 'unknown'
        
        # Extract court number
        court_match = re.search(r'Court\s*[:#]?\s*(\d+)', body, re.IGNORECASE)
        if court_match:
            booking_info['court'] = int(court_match.group(1))
        
        # Extract date (multiple formats)
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, body, re.IGNORECASE)
            if date_match:
                booking_info['date_str'] = date_match.group(0)
                break
        
        # Extract time
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*[AP]M)',
            r'(\d{1,2}:\d{2})\s*-\s*\d{1,2}:\d{2}',  # Range format
            r'at\s+(\d{1,2}:\d{2})'
        ]
        
        for pattern in time_patterns:
            time_match = re.search(pattern, body, re.IGNORECASE)
            if time_match:
                booking_info['time_str'] = time_match.group(1)
                break
        
        # Extract user/account email
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_matches = re.findall(email_pattern, body)
        
        # Look for NYU club tennis emails
        for email in email_matches:
            if 'nyuclubtennis' in email:
                booking_info['account_email'] = email
                break
        
        # Only return if we found some meaningful data
        if len(booking_info) > 1:  # More than just status
            return booking_info
        
        return None


if __name__ == "__main__":
    # Test the Gmail reader
    logging.basicConfig(level=logging.INFO)
    
    reader = GmailReader()
    emails = reader.get_booking_emails(days_back=7)
    
    print(f"Found {len(emails)} booking-related emails")
    for email in emails:
        print(f"\n{'-'*50}")
        print(f"Status: {email.get('status', 'Unknown')}")
        print(f"Court: {email.get('court', 'Unknown')}")
        print(f"Date: {email.get('date_str', 'Unknown')}")
        print(f"Time: {email.get('time_str', 'Unknown')}")
        print(f"Account: {email.get('account_email', 'Unknown')}")
        print(f"Subject: {email.get('subject', '')[:80]}")
