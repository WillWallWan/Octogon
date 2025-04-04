#!/usr/bin/env python3
"""
Manual Tennis Booker - Books secondary courts.
This script uses the same infrastructure as tennis_booker.py but books
the secondary court preferences (courts 1, 2, 4) instead of primary ones.
"""

import logging
from datetime import datetime, timedelta
# Import everything we need from the original tennis_booker
from tennis_booker import TennisBooker, is_valid_booking_time
from config import USERS, BOOKING_RULES

# Set up logging with the same format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('manual_tennis_booker.log'),
        logging.StreamHandler()
    ]
)

def main():
    """Main function to run the manual tennis court booking system.
    This version uses the SECOND court preference for each user."""
    if not is_valid_booking_time():
        logging.info("Not a valid booking time. Exiting.")
        return

    # Get today's weekday (0=Monday, 6=Sunday)
    today_weekday = datetime.now().weekday()
    
    # Get the days ahead to book based on today's weekday
    days_ahead_to_book = BOOKING_RULES.get(today_weekday, [2])  # Default to 2 days if not specified
    
    # For each booking day (on Friday this would be days 2, 3, and 4)
    for days_ahead in days_ahead_to_book:
        booking_date = datetime.now() + timedelta(days=days_ahead)
        logging.info(f"[MANUAL] Attempting to book for {booking_date.strftime('%A, %m/%d/%Y')} ({days_ahead} days ahead)")
        
        # For each user account
        for username, user_data in USERS.items():
            logging.info(f"[MANUAL] Processing user {username} for {booking_date.strftime('%m/%d/%Y')}")
            
            # Skip users without multiple court preferences or times
            if not user_data['preferred_courts'] or len(user_data['preferred_courts']) < 2 or not user_data['preferred_times']:
                logging.warning(f"[MANUAL] User {username} doesn't have a secondary court preference, skipping")
                continue
                
            # Use the SECOND court preference (index 1)
            secondary_court = user_data['preferred_courts'][1] if len(user_data['preferred_courts']) > 1 else None
            if not secondary_court:
                logging.warning(f"[MANUAL] No secondary court preference for {username}, skipping")
                continue
                
            # Use the first time preference
            preferred_time = user_data['preferred_times'][0]
            
            logging.info(f"[MANUAL] Trying to book SECONDARY court {secondary_court} at {preferred_time} for {username} on {booking_date.strftime('%m/%d/%Y')}")
            
            # Create a new booking session for each attempt
            booker = TennisBooker()
            try:
                if booker.setup_driver() and booker.login(user_data['email'], user_data['password']):
                    success = booker.book_court(
                        secondary_court,
                        booking_date,
                        preferred_time
                    )
                    
                    if success:
                        logging.info(f"[MANUAL] Successfully booked SECONDARY court {secondary_court} at {preferred_time} for {username} on {booking_date.strftime('%m/%d/%Y')}")
                    else:
                        logging.warning(f"[MANUAL] Could not book SECONDARY court {secondary_court} at {preferred_time} for {username} on {booking_date.strftime('%m/%d/%Y')}")
            finally:
                # Close each browser session
                booker.close()

if __name__ == "__main__":
    main() 