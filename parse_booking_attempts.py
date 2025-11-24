#!/usr/bin/env python3
"""
Parser for extracting booking attempts from auto_booker_action.log
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class BookingLogParser:
    def __init__(self, log_file='auto_booker_action.log'):
        self.log_file = log_file
        
    def parse_booking_attempts(self, target_date: Optional[datetime] = None) -> Dict:
        """
        Parse log file to extract all booking attempts for a specific date.
        
        Args:
            target_date: Date to filter logs (defaults to today)
            
        Returns:
            Dictionary with booking attempts organized by account
        """
        if target_date is None:
            target_date = datetime.now()
            
        # Format date for comparison
        date_str = target_date.strftime('%Y-%m-%d')
        
        booking_attempts = []
        script_start_time = None
        submission_time = None
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    # Check if line is from target date
                    if not line.startswith(date_str):
                        continue
                    
                    # Initialize variables
                    line_time = None
                    timestamp_str = None
                    
                    # Extract timestamp with milliseconds
                    timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3})', line)
                    if timestamp_match:
                        # Combine timestamp with milliseconds
                        timestamp_str = f"{timestamp_match.group(1)}.{timestamp_match.group(2)}"
                        line_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                    
                    # Detect script start
                    if "Script started" in line:
                        script_start_time = line_time
                        logger.info(f"Found script start at {script_start_time}")
                    
                    # Detect submission phase start
                    if "Target time reached! Starting RAPID Submission Phase" in line:
                        submission_time = line_time
                        logger.info(f"Found submission phase at {submission_time}")
                    
                    # Parse booking submission attempts
                    # Pattern: "Clicking submit for instance X/Y (Court Z on DATE at TIME) using EMAIL"
                    submit_pattern = r'Clicking submit for instance \d+/\d+ \(Court (\d+) on ([\d/\-]+) at (\d{2}:\d{2})\) using ([\w\+@\.]+)'
                    submit_match = re.search(submit_pattern, line)
                    
                    if submit_match and line_time and timestamp_str:
                        court = int(submit_match.group(1))
                        booking_date = submit_match.group(2)
                        time = submit_match.group(3)
                        email = submit_match.group(4)
                        
                        # Extract account alias
                        alias_match = re.search(r'nyuclubtennis\+(\w+)@', email)
                        account_alias = alias_match.group(1) if alias_match else email
                        
                        booking_attempt = {
                            'timestamp': line_time,
                            'timestamp_str': timestamp_str,  # Keep the full timestamp string with milliseconds
                            'court': court,
                            'booking_date': booking_date,
                            'time': time,
                            'email': email,
                            'account_alias': account_alias,
                            'status': 'submitted'
                        }
                        
                        booking_attempts.append(booking_attempt)
                        logger.debug(f"Found booking: {account_alias} → Court {court} at {time} on {booking_date}")
        
        except Exception as e:
            logger.error(f"Error parsing log file: {e}")
        
        # Organize by account
        by_account = defaultdict(list)
        for attempt in booking_attempts:
            by_account[attempt['account_alias']].append(attempt)
        
        # Summary statistics
        courts_attempted = defaultdict(int)
        times_attempted = defaultdict(int)
        
        for attempt in booking_attempts:
            courts_attempted[attempt['court']] += 1
            times_attempted[attempt['time']] += 1
        
        return {
            'date': date_str,
            'script_start': script_start_time,
            'submission_time': submission_time,
            'total_attempts': len(booking_attempts),
            'attempts': booking_attempts,
            'by_account': dict(by_account),
            'courts_attempted': dict(courts_attempted),
            'times_attempted': dict(times_attempted)
        }
    
    def display_summary(self, parsed_data: Dict):
        """Display a formatted summary of booking attempts."""
        print(f"\n📋 BOOKING ATTEMPTS SUMMARY - {parsed_data['date']}")
        print("=" * 80)
        print(f"Script started: {parsed_data['script_start']}")
        print(f"Submission time: {parsed_data['submission_time']}")
        print(f"Total attempts: {parsed_data['total_attempts']}")
        
        print("\n📊 ATTEMPTS BY ACCOUNT:")
        print("-" * 80)
        for account, attempts in sorted(parsed_data['by_account'].items()):
            print(f"\n{account}:")
            for attempt in attempts:
                print(f"  → Court {attempt['court']} at {attempt['time']} on {attempt['booking_date']}")
        
        print("\n📊 COURTS ATTEMPTED:")
        print("-" * 80)
        for court, count in sorted(parsed_data['courts_attempted'].items()):
            print(f"Court {court}: {count} attempts")
        
        print("\n📊 TIMES ATTEMPTED:")
        print("-" * 80)
        for time, count in sorted(parsed_data['times_attempted'].items()):
            print(f"{time}: {count} attempts")


def main():
    """Test the parser."""
    logging.basicConfig(level=logging.INFO)
    
    parser = BookingLogParser()
    
    # Parse today's attempts
    print("Parsing today's booking attempts...")
    data = parser.parse_booking_attempts()
    
    # Display summary
    parser.display_summary(data)
    
    # Show a few specific examples
    if data['attempts']:
        print("\n\nFirst 5 booking attempts:")
        print("-" * 80)
        for i, attempt in enumerate(data['attempts'][:5]):
            print(f"{i+1}. {attempt['timestamp'].strftime('%H:%M:%S')} - "
                  f"{attempt['account_alias']} → Court {attempt['court']} "
                  f"at {attempt['time']} on {attempt['booking_date']}")


if __name__ == "__main__":
    main()






