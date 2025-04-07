#!/usr/bin/env python3
"""
Manual Tennis Booker - Books secondary courts.
This script uses the same infrastructure as tennis_booker.py but books
the secondary court preferences (courts 1, 2, 4) instead of primary ones.
"""

import logging
import random
from datetime import datetime, timedelta
# Import everything we need from the original tennis_booker
from tennis_booker import TennisBooker, is_valid_booking_time
from config import USERS, BOOKING_RULES, SECONDARY_COURT_PRIORITIES

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
    This version uses randomized account assignments for secondary courts."""
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
        
        # Get list of available accounts and shuffle them for random assignment
        available_accounts = list(USERS.keys())
        random.shuffle(available_accounts)
        
        # Track which accounts we've used for this booking day
        used_accounts = set()
        
        # Go through secondary court priorities in order
        for priority in SECONDARY_COURT_PRIORITIES:
            court_number = priority["court"]
            preferred_time = priority["time"]
            
            logging.info(f"[MANUAL] Attempting to book secondary court {court_number} at {preferred_time}")
            
            # Find an account that hasn't been used yet
            for username in available_accounts:
                if username not in used_accounts:
                    user_data = USERS[username]
                    logging.info(f"[MANUAL] Selected user {username} to attempt booking court {court_number}")
                    
                    # Create a new booking session
                    booker = TennisBooker()
                    try:
                        if booker.setup_driver() and booker.login(user_data['email'], user_data['password']):
                            success = booker.book_court(
                                court_number,
                                booking_date,
                                preferred_time
                            )
                            
                            if success:
                                # Add to used accounts so we don't reuse it
                                used_accounts.add(username)
                                logging.info(f"[MANUAL] Successfully booked court {court_number} at {preferred_time} with {username} for {booking_date.strftime('%m/%d/%Y')}")
                                break  # Move to next priority
                            else:
                                logging.warning(f"[MANUAL] User {username} could not book court {court_number} at {preferred_time}")
                    except Exception as e:
                        logging.error(f"[MANUAL] Error with user {username}: {str(e)}")
                    finally:
                        booker.close()
            else:
                # If we tried all available accounts and none worked, log it
                logging.warning(f"[MANUAL] Could not book court {court_number} at {preferred_time} with any available account")
        
        # Log summary
        logging.info(f"[MANUAL] Booking complete for {booking_date.strftime('%m/%d/%Y')} - Used accounts: {used_accounts}")

if __name__ == "__main__":
    main() 