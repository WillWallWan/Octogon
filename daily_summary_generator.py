#!/usr/bin/env python3
"""
Daily summary generator for tennis court bookings.
Combines log data and email confirmations to generate comprehensive summaries.
"""
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import Optional
import json

from gmail_reader import GmailReader
from log_parser import LogParser
from llm_summarizer import LLMSummarizer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('daily_summary.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DailySummaryGenerator:
    def __init__(self, 
                 gmail_credentials='credentials.json',
                 log_file='auto_booker_action.log',
                 llm_provider='openai',
                 llm_api_key=None):
        """
        Initialize the summary generator.
        
        Args:
            gmail_credentials: Path to Gmail API credentials file
            log_file: Path to the booking log file
            llm_provider: 'openai' or 'anthropic'
            llm_api_key: API key for LLM provider
        """
        self.gmail_reader = GmailReader(credentials_file=gmail_credentials)
        self.log_parser = LogParser(log_file=log_file)
        self.llm_summarizer = LLMSummarizer(provider=llm_provider, api_key=llm_api_key)
        
    def generate_summary(self, date: Optional[datetime] = None) -> str:
        """
        Generate a comprehensive summary for a specific date.
        
        Args:
            date: Date to generate summary for (defaults to today)
            
        Returns:
            Summary text
        """
        if date is None:
            date = datetime.now()
            
        logger.info(f"Generating summary for {date.strftime('%Y-%m-%d')}")
        
        # Parse log data
        logger.info("Parsing log file...")
        log_summary = self.log_parser.get_session_summary(date)
        logger.info(f"Found {log_summary['total_attempts']} booking attempts in logs")
        
        # Fetch and parse emails
        logger.info("Fetching emails...")
        email_data = self.gmail_reader.get_booking_emails(days_back=1)
        logger.info(f"Found {len(email_data)} booking-related emails")
        
        # Generate summary using LLM
        logger.info("Generating summary...")
        summary = self.llm_summarizer.generate_summary(log_summary, email_data)
        
        return summary
    
    def save_summary(self, summary: str, date: Optional[datetime] = None):
        """Save summary to file."""
        if date is None:
            date = datetime.now()
            
        filename = f"summaries/booking_summary_{date.strftime('%Y%m%d')}.txt"
        os.makedirs('summaries', exist_ok=True)
        
        with open(filename, 'w') as f:
            f.write(summary)
            
        logger.info(f"Summary saved to {filename}")
        
    def send_summary_email(self, summary: str, recipients: list):
        """
        Send summary via email (requires additional email sending setup).
        
        This is a placeholder - implement based on your email sending preferences.
        """
        logger.info("Email sending not yet implemented")
        # TODO: Implement email sending
        pass
    
    def run_daily_summary(self):
        """Run the complete daily summary process."""
        try:
            # Generate summary for today
            summary = self.generate_summary()
            
            # Save to file
            self.save_summary(summary)
            
            # Log summary to console
            logger.info("\n" + "="*50 + "\nDAILY SUMMARY\n" + "="*50)
            logger.info(summary)
            
            # Optionally send email
            # self.send_summary_email(summary, ['your-email@example.com'])
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            raise


def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description='Generate daily tennis booking summary')
    parser.add_argument(
        '--date',
        type=str,
        help='Date to generate summary for (YYYY-MM-DD format, defaults to today)'
    )
    parser.add_argument(
        '--provider',
        type=str,
        choices=['openai', 'anthropic'],
        default='openai',
        help='LLM provider to use'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='API key for LLM provider (defaults to environment variable)'
    )
    parser.add_argument(
        '--gmail-creds',
        type=str,
        default='credentials.json',
        help='Path to Gmail API credentials file'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default='auto_booker_action.log',
        help='Path to booking log file'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for summary (optional)'
    )
    
    args = parser.parse_args()
    
    # Parse date if provided
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid date format: {args.date}")
            sys.exit(1)
    
    # Check for required files
    if not os.path.exists(args.log_file):
        logger.error(f"Log file not found: {args.log_file}")
        sys.exit(1)
    
    # Check for API key
    api_key = args.api_key
    if not api_key:
        env_var = f"{args.provider.upper()}_API_KEY"
        api_key = os.environ.get(env_var)
        if not api_key:
            logger.warning(f"No API key found. Set {env_var} environment variable or use --api-key")
            logger.info("Will use fallback summary generation without LLM")
    
    # Initialize generator
    try:
        generator = DailySummaryGenerator(
            gmail_credentials=args.gmail_creds,
            log_file=args.log_file,
            llm_provider=args.provider,
            llm_api_key=api_key
        )
    except Exception as e:
        logger.error(f"Failed to initialize summary generator: {e}")
        logger.info("Make sure you have set up Gmail API credentials (see README)")
        sys.exit(1)
    
    # Generate summary
    try:
        summary = generator.generate_summary(target_date)
        
        # Save if output file specified
        if args.output:
            with open(args.output, 'w') as f:
                f.write(summary)
            logger.info(f"Summary written to {args.output}")
        else:
            # Save to default location
            generator.save_summary(summary, target_date)
            
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()





