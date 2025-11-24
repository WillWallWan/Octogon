#!/usr/bin/env python3
"""
Combine booking attempts from logs with email results to create a comprehensive summary
"""
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import argparse

from gmail_reader import GmailReader
from parse_booking_attempts import BookingLogParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BookingResultsCombiner:
    def __init__(self):
        self.gmail_reader = GmailReader()
        self.log_parser = BookingLogParser()
        
    def combine_results(self, date: datetime = None) -> dict:
        """Combine log attempts with email results."""
        if date is None:
            date = datetime.now()
            
        # Parse log attempts
        logger.info("Parsing booking attempts from logs...")
        log_data = self.log_parser.parse_booking_attempts(date)
        
        # Get email results
        logger.info("Fetching email results...")
        service = self.gmail_reader._get_gmail_service()
        email_results = self.analyze_emails_for_date(service, date)
        
        # Combine the data
        combined = self.match_attempts_with_results(log_data, email_results)
        
        return combined
    
    def analyze_emails_for_date(self, service, date: datetime) -> dict:
        """Get email results for a specific date."""
        # For booking attempts on date X, emails arrive on date X
        # Search for emails from today
        after_date = date.strftime('%Y/%m/%d')
        before_date = (date + timedelta(days=1)).strftime('%Y/%m/%d')
        
        query = f'from:donotreply@notify.civicpermits.com after:{after_date} before:{before_date}'
        
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=100
        ).execute()
        
        messages = results.get('messages', [])
        
        email_by_account = defaultdict(list)
        
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            to_field = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract account alias
            import re
            alias_match = re.search(r'nyuclubtennis\+(\w+)@', to_field)
            if alias_match:
                account = alias_match.group(1)
                
                # Categorize result and email type
                if "Your Tennis Permit has been approved" in subject:
                    result = 'approved'
                    email_type = 'final_decision'
                elif "Unable to Process your request" in subject:
                    result = 'rejected'
                    email_type = 'final_decision'
                elif "Your permit request has been canceled" in subject:
                    result = 'canceled'
                    email_type = 'final_decision'
                elif "Pending Approval" in subject or "application has been received" in subject:
                    result = 'pending'
                    email_type = 'submission_confirmation'
                else:
                    result = 'unknown'
                    email_type = 'unknown'
                
                email_by_account[account].append({
                    'result': result,
                    'email_type': email_type,
                    'subject': subject,
                    'time': date_str
                })
        
        return dict(email_by_account)
    
    def match_attempts_with_results(self, log_data: dict, email_results: dict) -> dict:
        """Match booking attempts with email results."""
        combined = {
            'date': log_data['date'],
            'submission_time': log_data['submission_time'],
            'total_attempts': log_data['total_attempts'],
            'by_account': {},
            'summary': {
                'approved_bookings': [],
                'rejected_bookings': [],
                'unknown_bookings': [],
                'success_by_court': defaultdict(lambda: {'attempts': 0, 'successes': 0}),
                'success_by_time': defaultdict(lambda: {'attempts': 0, 'successes': 0})
            }
        }
        
        # Process each account
        for account, attempts in log_data['by_account'].items():
            account_results = email_results.get(account, [])
            
            # Count results by type and email category
            approved_count = sum(1 for r in account_results if r['result'] == 'approved')
            rejected_count = sum(1 for r in account_results if r['result'] == 'rejected')
            canceled_count = sum(1 for r in account_results if r['result'] == 'canceled')
            pending_count = sum(1 for r in account_results if r['result'] == 'pending')
            
            # Count email types
            submission_confirmations = sum(1 for r in account_results if r['email_type'] == 'submission_confirmation')
            final_decisions = sum(1 for r in account_results if r['email_type'] == 'final_decision')
            
            combined['by_account'][account] = {
                'attempts': attempts,
                'email_results': account_results,
                'approved_count': approved_count,
                'rejected_count': rejected_count,
                'canceled_count': canceled_count,
                'pending_count': pending_count,
                'submission_confirmations': submission_confirmations,
                'final_decisions': final_decisions
            }
            
            # Assign results to specific bookings
            # Strategy: If an account has 1 approval and 1 rejection, we can't know which booking succeeded
            # We'll mark them as probable success/failure
            for i, attempt in enumerate(attempts):
                court = attempt['court']
                time = attempt['time']
                
                # Update attempt counts
                combined['summary']['success_by_court'][court]['attempts'] += 1
                combined['summary']['success_by_time'][time]['attempts'] += 1
                
                # Determine result using dual-email approach
                if submission_confirmations == 0:
                    # No submission confirmation = technical failure
                    booking_result = 'failed (no confirmation received)'
                elif final_decisions == 0:
                    # Submission confirmed but no decision = still pending or lost
                    booking_result = 'unknown (confirmed but no decision)'
                elif approved_count > 0 and rejected_count == 0 and canceled_count == 0:
                    # Pure success
                    booking_result = 'approved'
                elif approved_count == 0 and (rejected_count > 0 or canceled_count > 0):
                    # Pure failure
                    if canceled_count > 0:
                        booking_result = 'canceled (too early)'
                    else:
                        booking_result = 'rejected (too late)'
                else:
                    # Mixed results
                    booking_result = f'unknown (mixed: {approved_count}✅ {rejected_count}❌ {canceled_count}🚫)'
                
                booking_info = {
                    'account': account,
                    'court': court,
                    'time': time,
                    'date': attempt['booking_date'],
                    'result': booking_result
                }
                
                if booking_result == 'approved':
                    combined['summary']['approved_bookings'].append(booking_info)
                    combined['summary']['success_by_court'][court]['successes'] += 1
                    combined['summary']['success_by_time'][time]['successes'] += 1
                elif booking_result == 'rejected':
                    combined['summary']['rejected_bookings'].append(booking_info)
                else:
                    combined['summary']['unknown_bookings'].append(booking_info)
        
        return combined
    
    def generate_summary_text(self, combined_data: dict) -> str:
        """Generate a human-readable summary."""
        # Calculate overall statistics
        total_confirmations = sum(data.get('submission_confirmations', 0) for data in combined_data['by_account'].values())
        total_decisions = sum(data.get('final_decisions', 0) for data in combined_data['by_account'].values())
        total_approved = sum(data['approved_count'] for data in combined_data['by_account'].values())
        total_rejected = sum(data['rejected_count'] for data in combined_data['by_account'].values())
        total_canceled = sum(data.get('canceled_count', 0) for data in combined_data['by_account'].values())
        
        summary = f"""
TENNIS BOOKING SUMMARY - {combined_data['date']}
================================================================================

OVERALL RESULTS:
- Total booking attempts: {combined_data['total_attempts']}
- Submission confirmations received: {total_confirmations}/{combined_data['total_attempts']} ({total_confirmations/combined_data['total_attempts']*100:.1f}%)
- Final decisions received: {total_decisions}/{combined_data['total_attempts']} ({total_decisions/combined_data['total_attempts']*100:.1f}%)
- Confirmed successful: {total_approved}
- Confirmed failed: {total_rejected + total_canceled} (rejected: {total_rejected}, canceled: {total_canceled})
- Still pending/unknown: {combined_data['total_attempts'] - total_decisions}

SUBMISSION RESULTS (ordered by time):
Legend: ✅=Approved ❌=Failed (too late/too early) 🚫=No confirmation ❓=Pending/Mixed
"""
        
        # Get all attempts with results
        all_attempts_with_results = []
        for account, data in combined_data['by_account'].items():
            for attempt in data['attempts']:
                # Determine result using dual-email approach
                result_emoji = ""
                submission_confirmations = data.get('submission_confirmations', 0)
                final_decisions = data.get('final_decisions', 0)
                approved = data['approved_count']
                rejected = data['rejected_count'] 
                canceled = data.get('canceled_count', 0)
                
                if submission_confirmations == 0:
                    # No submission confirmation = technical failure
                    result_emoji = "🚫"
                elif final_decisions == 0:
                    # Submission confirmed but no decision = still pending
                    result_emoji = "❓"
                elif approved > 0 and rejected == 0 and canceled == 0:
                    # Pure success
                    result_emoji = "✅"
                elif approved == 0 and (rejected > 0 or canceled > 0):
                    # Pure failure - both use ❌ but we can distinguish in tooltips
                    result_emoji = "❌"  # Too late (rejected) or too early (canceled)
                else:
                    # Mixed results
                    result_emoji = "❓"
                
                attempt_with_result = attempt.copy()
                attempt_with_result['account'] = account
                attempt_with_result['result_emoji'] = result_emoji
                attempt_with_result['approved_count'] = data['approved_count']
                attempt_with_result['rejected_count'] = data['rejected_count']
                all_attempts_with_results.append(attempt_with_result)
        
        # Sort by timestamp
        all_attempts_with_results.sort(key=lambda x: x['timestamp'])
        
        # Display all attempts
        for i, attempt in enumerate(all_attempts_with_results):
            submit_time = attempt['timestamp'].strftime('%H:%M:%S.%f')[:-3]
            summary += f"\n{i+1:2d}. {submit_time} {attempt['result_emoji']} {attempt['account']:>10} → Court {attempt['court']} at {attempt['time']} on {attempt['booking_date']}"
        
        # Add account summary
        summary += "\n\nACCOUNT SUMMARY:\n"
        # Categorize accounts by their email status
        successful_accounts = []
        failed_accounts = []
        canceled_accounts = []
        mixed_accounts = []
        no_confirmation_accounts = []
        pending_accounts = []
        
        for account, data in combined_data['by_account'].items():
            approved = data['approved_count']
            rejected = data['rejected_count'] 
            canceled = data.get('canceled_count', 0)
            confirmations = data.get('submission_confirmations', 0)
            decisions = data.get('final_decisions', 0)
            
            if confirmations == 0:
                # No submission confirmation received
                no_confirmation_accounts.append(account)
            elif decisions == 0:
                # Confirmed but no final decision
                pending_accounts.append(account)
            elif approved > 0 and rejected == 0 and canceled == 0:
                successful_accounts.append(account)
            elif approved == 0 and rejected > 0 and canceled == 0:
                failed_accounts.append(account)
            elif approved == 0 and rejected == 0 and canceled > 0:
                canceled_accounts.append(account)
            else:
                mixed_accounts.append(account)
        
        if successful_accounts:
            summary += f"✅ Submission Confirmed + Approved: {', '.join(sorted(successful_accounts))}\n"
        if failed_accounts:
            summary += f"❌ Submission Confirmed + Unable to Process (too late): {', '.join(sorted(failed_accounts))}\n"
        if canceled_accounts:
            summary += f"❌ Submission Confirmed + Cancelled (too early): {', '.join(sorted(canceled_accounts))}\n"
        if pending_accounts:
            summary += f"❓ Submission Confirmed + No Decision (pending): {', '.join(sorted(pending_accounts))}\n"
        if no_confirmation_accounts:
            summary += f"🚫 No Submission Confirmation (technical failure): {', '.join(sorted(no_confirmation_accounts))}\n"
        if mixed_accounts:
            summary += f"❓ Mixed results (multiple outcomes): {', '.join(sorted(mixed_accounts))}\n"
        
        # Court performance
        summary += "\nBY COURT SUCCESS RATE:\n"
        for court, stats in sorted(combined_data['summary']['success_by_court'].items()):
            if stats['attempts'] > 0:
                rate = (stats['successes'] / stats['attempts']) * 100
                summary += f"  Court {court}: {stats['successes']}/{stats['attempts']} ({rate:.0f}%)\n"
        
        # Time slot performance
        summary += "\nBY TIME SLOT SUCCESS RATE:\n"
        for time, stats in sorted(combined_data['summary']['success_by_time'].items()):
            if stats['attempts'] > 0:
                rate = (stats['successes'] / stats['attempts']) * 100
                summary += f"  {time}: {stats['successes']}/{stats['attempts']} ({rate:.0f}%)\n"
        
        # Confirmed bookings
        if combined_data['summary']['approved_bookings']:
            summary += "\nCONFIRMED BOOKINGS:\n"
            for booking in combined_data['summary']['approved_bookings']:
                summary += f"  ✅ {booking['account']} → Court {booking['court']} at {booking['time']} on {booking['date']}\n"
        
        # Add explanation about dual-email tracking
        if no_confirmation_accounts or pending_accounts:
            summary += f"\nEMAIL TRACKING ANALYSIS:\n"
            
            if no_confirmation_accounts:
                summary += f"🚫 No submission confirmation: {', '.join(sorted(no_confirmation_accounts))}\n"
                summary += "   These accounts likely had technical failures - submissions never reached the server.\n"
                
            if pending_accounts:
                summary += f"❓ Confirmed but no decision: {', '.join(sorted(pending_accounts))}\n"
                summary += "   These submissions were received but no final decision email arrived yet.\n"
                
            summary += f"\nTIMING INSIGHTS FROM 5-CATEGORY ANALYSIS:\n"
            if no_confirmation_accounts:
                summary += "🚫 No confirmation = Technical issues or submissions never reached server\n"
            if canceled_accounts:
                summary += "❌ Confirmed + Cancelled = Submissions were TOO EARLY (server not ready)\n"
            if failed_accounts:
                summary += "❌ Confirmed + Unable to Process = Submissions were TOO LATE (courts taken)\n"
            if pending_accounts:
                summary += "❓ Confirmed + No Decision = Server received but still processing\n"
            if successful_accounts:
                summary += "✅ Confirmed + Approved = PERFECT TIMING!\n"
        
        # Analyze timing patterns to find sweet spot
        summary += self._analyze_timing_sweet_spot(combined_data)
        
        return summary
    
    def _analyze_timing_sweet_spot(self, combined_data):
        """Analyze timing patterns to find the sweet spot between too early and too late."""
        timing_analysis = "\n\n🎯 TIMING ANALYSIS - FINDING THE SWEET SPOT:\n"
        timing_analysis += "=" * 60 + "\n"
        
        # Collect all attempts with their results and exact timing
        timing_data = []
        for account, data in combined_data['by_account'].items():
            for attempt in data['attempts']:
                # Determine the final result for this account
                result_type = 'unknown'
                if data.get('submission_confirmations', 0) == 0:
                    result_type = 'no_confirmation'
                elif data.get('canceled_count', 0) > 0 and data['rejected_count'] == 0:
                    result_type = 'canceled'
                elif data['rejected_count'] > 0 and data.get('canceled_count', 0) == 0:
                    result_type = 'rejected'
                elif data['approved_count'] > 0:
                    result_type = 'approved'
                elif data.get('final_decisions', 0) == 0:
                    result_type = 'pending'
                else:
                    result_type = 'mixed'
                
                timing_data.append({
                    'timestamp': attempt['timestamp'],
                    'time_str': attempt['timestamp'].strftime('%H:%M:%S.%f')[:-3],
                    'account': account,
                    'court': attempt['court'],
                    'result': result_type
                })
        
        # Sort by timestamp
        timing_data.sort(key=lambda x: x['timestamp'])
        
        # Group by result type
        earliest_by_type = {}
        latest_by_type = {}
        count_by_type = defaultdict(int)
        
        for item in timing_data:
            result = item['result']
            count_by_type[result] += 1
            
            if result not in earliest_by_type or item['timestamp'] < earliest_by_type[result]['timestamp']:
                earliest_by_type[result] = item
            
            if result not in latest_by_type or item['timestamp'] > latest_by_type[result]['timestamp']:
                latest_by_type[result] = item
        
        # Display timing ranges
        if 'canceled' in earliest_by_type:
            timing_analysis += f"\n❌ CANCELLED (Too Early):\n"
            timing_analysis += f"   Earliest: {earliest_by_type['canceled']['time_str']} ({earliest_by_type['canceled']['account']})\n"
            timing_analysis += f"   Latest:   {latest_by_type['canceled']['time_str']} ({latest_by_type['canceled']['account']})\n"
            timing_analysis += f"   Count:    {count_by_type['canceled']} submissions\n"
        
        if 'approved' in earliest_by_type:
            timing_analysis += f"\n✅ APPROVED (Perfect Timing):\n"
            timing_analysis += f"   Earliest: {earliest_by_type['approved']['time_str']} ({earliest_by_type['approved']['account']})\n"
            timing_analysis += f"   Latest:   {latest_by_type['approved']['time_str']} ({latest_by_type['approved']['account']})\n"
            timing_analysis += f"   Count:    {count_by_type['approved']} submissions\n"
        
        if 'rejected' in earliest_by_type:
            timing_analysis += f"\n❌ REJECTED/Unable to Process (Too Late):\n"
            timing_analysis += f"   Earliest: {earliest_by_type['rejected']['time_str']} ({earliest_by_type['rejected']['account']})\n"
            timing_analysis += f"   Latest:   {latest_by_type['rejected']['time_str']} ({latest_by_type['rejected']['account']})\n"
            timing_analysis += f"   Count:    {count_by_type['rejected']} submissions\n"
        
        # Calculate sweet spot
        timing_analysis += f"\n🎯 SWEET SPOT ANALYSIS:\n"
        
        if 'canceled' in latest_by_type and 'rejected' in earliest_by_type:
            # There's overlap - need to find the gap
            last_canceled = latest_by_type['canceled']['timestamp']
            first_rejected = earliest_by_type['rejected']['timestamp']
            
            if last_canceled < first_rejected:
                gap_ms = (first_rejected - last_canceled).total_seconds() * 1000
                timing_analysis += f"   Gap detected between too early and too late:\n"
                timing_analysis += f"   Last cancelled: {latest_by_type['canceled']['time_str']}\n"
                timing_analysis += f"   First rejected: {earliest_by_type['rejected']['time_str']}\n"
                timing_analysis += f"   Sweet spot window: {gap_ms:.0f}ms\n"
            else:
                timing_analysis += f"   ⚠️  OVERLAP DETECTED - No clear sweet spot!\n"
                timing_analysis += f"   Some submissions were cancelled while others submitted later were rejected.\n"
                timing_analysis += f"   This suggests server readiness varies or other factors are at play.\n"
        
        if 'approved' in earliest_by_type:
            timing_analysis += f"\n   ✅ Successful timing window:\n"
            timing_analysis += f"   From: {earliest_by_type['approved']['time_str']}\n"
            timing_analysis += f"   To:   {latest_by_type['approved']['time_str']}\n"
        
        # Recommendations
        timing_analysis += f"\n💡 RECOMMENDATIONS:\n"
        
        if 'canceled' in count_by_type and count_by_type['rejected'] in count_by_type:
            if count_by_type['canceled'] > count_by_type['rejected']:
                timing_analysis += "   - Submissions are generally too early. Consider delaying.\n"
            elif count_by_type['rejected'] > count_by_type['canceled']:
                timing_analysis += "   - Submissions are generally too late. Consider submitting earlier.\n"
        elif 'canceled' in count_by_type:
            timing_analysis += "   - All failed submissions were too early. Need to delay significantly.\n"
        elif 'rejected' in count_by_type:
            timing_analysis += "   - All failed submissions were too late. Need to submit earlier.\n"
        
        if 'approved' in earliest_by_type:
            approved_time = earliest_by_type['approved']['timestamp']
            base_time = approved_time.replace(hour=8, minute=0, second=0, microsecond=0)
            optimal_delay = (approved_time - base_time).total_seconds()
            timing_analysis += f"   - Optimal submission time appears to be 8:00:00 + {optimal_delay:.3f} seconds\n"
        
        return timing_analysis


def main():
    """Run the combined analysis."""
    parser = argparse.ArgumentParser(description='Analyze tennis booking results for a specific date')
    parser.add_argument(
        '--date',
        type=str,
        help='Date to analyze (YYYY-MM-DD format). Defaults to today.',
        default=None
    )
    args = parser.parse_args()
    
    # Parse date if provided
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
            print(f"Analyzing bookings for {args.date}")
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'. Please use YYYY-MM-DD format.")
            sys.exit(1)
    else:
        target_date = datetime.now()
        print(f"Analyzing today's bookings ({target_date.strftime('%Y-%m-%d')})")
    
    combiner = BookingResultsCombiner()
    
    print("Combining booking attempts with email results...")
    combined = combiner.combine_results(date=target_date)
    
    # Generate and print summary
    summary = combiner.generate_summary_text(combined)
    print(summary)
    
    # Save to file
    filename = f"booking_summary_{target_date.strftime('%Y%m%d')}.txt"
    with open(filename, 'w') as f:
        f.write(summary)
    print(f"\nSummary saved to {filename}")


if __name__ == "__main__":
    main()
