"""
Parser for extracting booking attempts and results from auto_booker_action.log
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class LogParser:
    def __init__(self, log_file='auto_booker_action.log'):
        self.log_file = log_file
        
    def parse_booking_attempts(self, date: Optional[datetime] = None) -> List[Dict]:
        """
        Parse log file to extract all booking attempts.
        
        Args:
            date: Optional date to filter logs (defaults to today)
            
        Returns:
            List of booking attempt dictionaries
        """
        if date is None:
            date = datetime.now()
            
        attempts = []
        current_session = None
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    # Check if line is from the target date
                    line_date = self._extract_date(line)
                    if line_date and line_date.date() != date.date():
                        continue
                    
                    # Detect session start
                    if "Script started" in line:
                        current_session = {
                            'start_time': line_date,
                            'attempts': []
                        }
                    
                    # Parse booking attempts
                    attempt = self._parse_attempt_line(line)
                    if attempt and current_session:
                        attempts.append(attempt)
                    
                    # Parse submission results
                    if "SUBMISSION RESULT" in line:
                        result = self._parse_submission_result(line)
                        if result:
                            # Try to match with recent attempt
                            for attempt in reversed(attempts[-10:]):
                                if (attempt.get('court') == result.get('court') and
                                    attempt.get('time') == result.get('time')):
                                    attempt.update(result)
                                    break
                    
                    # Parse success messages
                    if "Successfully booked" in line:
                        success_info = self._parse_success_line(line)
                        if success_info:
                            for attempt in reversed(attempts[-10:]):
                                if (attempt.get('court') == success_info.get('court') and
                                    attempt.get('time') == success_info.get('time')):
                                    attempt['status'] = 'success'
                                    attempt['confirmation'] = success_info.get('confirmation')
                                    break
                    
                    # Parse error messages
                    if "ERROR -" in line or "Failed to book" in line:
                        error_info = self._parse_error_line(line)
                        if error_info:
                            for attempt in reversed(attempts[-5:]):
                                if not attempt.get('status'):
                                    attempt['status'] = 'failed'
                                    attempt['error'] = error_info.get('error')
                                    break
                    
        except Exception as e:
            logger.error(f"Error parsing log file: {e}")
        
        return attempts
    
    def _extract_date(self, line: str) -> Optional[datetime]:
        """Extract datetime from log line."""
        date_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), '%Y-%m-%d %H:%M:%S')
            except:
                pass
        return None
    
    def _parse_attempt_line(self, line: str) -> Optional[Dict]:
        """Parse lines indicating booking attempts."""
        attempt_patterns = [
            # Pattern for "Attempting to book Court X on date at time"
            r'Attempting to book Court (\d+) on ([\d-/]+) at (\d{2}:\d{2})',
            # Pattern for "Booking Court X for date at time"
            r'Booking Court (\d+) for ([\d-/]+) at (\d{2}:\d{2})',
            # Pattern for parallel booking attempts
            r'Starting (\d+)/\d+ parallel.*Court (\d+) on ([\d-/]+) at (\d{2}:\d{2})'
        ]
        
        for pattern in attempt_patterns:
            match = re.search(pattern, line)
            if match:
                if 'Starting' in pattern:
                    # Parallel booking pattern has different group ordering
                    court = int(match.group(2))
                    date_str = match.group(3)
                    time_str = match.group(4)
                else:
                    court = int(match.group(1))
                    date_str = match.group(2)
                    time_str = match.group(3)
                
                # Extract account email if present
                email_match = re.search(r'(nyuclubtennis\+\w+@gmail\.com)', line)
                
                return {
                    'timestamp': self._extract_date(line),
                    'court': court,
                    'date': date_str,
                    'time': time_str,
                    'account_email': email_match.group(1) if email_match else None,
                    'status': 'attempted'
                }
        
        return None
    
    def _parse_submission_result(self, line: str) -> Optional[Dict]:
        """Parse submission result lines."""
        # Extract court and time from submission result
        court_match = re.search(r'Court (\d+)', line)
        time_match = re.search(r'at (\d{2}:\d{2})', line)
        
        result = {}
        if court_match:
            result['court'] = int(court_match.group(1))
        if time_match:
            result['time'] = time_match.group(1)
        
        if 'SUCCESS' in line:
            result['status'] = 'submitted'
        elif 'FAILED' in line or 'ERROR' in line:
            result['status'] = 'failed'
            # Extract error message
            error_match = re.search(r'Error: (.+?)(?:\.|$)', line)
            if error_match:
                result['error'] = error_match.group(1).strip()
        
        return result if result else None
    
    def _parse_success_line(self, line: str) -> Optional[Dict]:
        """Parse successful booking confirmation lines."""
        # Pattern: Successfully booked Court X on date at time
        match = re.search(r'Successfully booked Court (\d+) on ([\d-/]+) at (\d{2}:\d{2})', line)
        if match:
            return {
                'court': int(match.group(1)),
                'date': match.group(2),
                'time': match.group(3),
                'status': 'success'
            }
        return None
    
    def _parse_error_line(self, line: str) -> Optional[Dict]:
        """Parse error lines."""
        error_patterns = [
            r'Court (\d+).*unavailable',
            r'Failed to book.*Court (\d+)',
            r'Error.*Court (\d+)'
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return {
                    'court': int(match.group(1)),
                    'error': line.strip()
                }
        
        # Generic error
        if 'ERROR' in line or 'Failed' in line:
            return {'error': line.strip()}
        
        return None
    
    def get_session_summary(self, date: Optional[datetime] = None) -> Dict:
        """
        Get a summary of booking attempts for a specific date.
        
        Returns:
            Dictionary with summary statistics
        """
        attempts = self.parse_booking_attempts(date)
        
        summary = {
            'total_attempts': len(attempts),
            'successful': 0,
            'failed': 0,
            'unknown': 0,
            'by_court': {},
            'by_account': {},
            'attempts': attempts
        }
        
        for attempt in attempts:
            status = attempt.get('status', 'unknown')
            if status == 'success':
                summary['successful'] += 1
            elif status in ['failed', 'error']:
                summary['failed'] += 1
            else:
                summary['unknown'] += 1
            
            # Count by court
            court = attempt.get('court')
            if court:
                if court not in summary['by_court']:
                    summary['by_court'][court] = {'attempts': 0, 'successes': 0}
                summary['by_court'][court]['attempts'] += 1
                if status == 'success':
                    summary['by_court'][court]['successes'] += 1
            
            # Count by account
            account = attempt.get('account_email')
            if account:
                if account not in summary['by_account']:
                    summary['by_account'][account] = {'attempts': 0, 'successes': 0}
                summary['by_account'][account]['attempts'] += 1
                if status == 'success':
                    summary['by_account'][account]['successes'] += 1
        
        return summary


if __name__ == "__main__":
    # Test the log parser
    logging.basicConfig(level=logging.INFO)
    
    parser = LogParser()
    summary = parser.get_session_summary()
    
    print(f"Total attempts: {summary['total_attempts']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Unknown: {summary['unknown']}")
    
    print("\nBy Court:")
    for court, stats in summary['by_court'].items():
        print(f"  Court {court}: {stats['attempts']} attempts, {stats['successes']} successes")
    
    print("\nBy Account:")
    for account, stats in summary['by_account'].items():
        print(f"  {account}: {stats['attempts']} attempts, {stats['successes']} successes")





