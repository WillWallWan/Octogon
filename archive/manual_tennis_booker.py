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
    This version uses a simplified linear account/court assignment approach."""
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
        
        # Get list of available accounts and shuffle them
        accounts = list(USERS.keys())
        random.shuffle(accounts)
        
        # Keep track of which accounts we've used
        used_accounts = []
        
        # Process each priority with a different account
        for i, priority in enumerate(SECONDARY_COURT_PRIORITIES):
            # Check if we have any accounts left
            if i >= len(accounts):
                logging.warning(f"[MANUAL] No more accounts available for priority #{i+1}")
                break
                
            # Get the next account
            username = accounts[i]
            user_data = USERS[username]
            
            # Get court and time from priority
            court_number = priority["court"]
            preferred_time = priority["time"]
            
            logging.info(f"[MANUAL] Priority #{i+1}: Assigning {username} to book court {court_number} at {preferred_time}")
            
            # Create booking session
            booker = TennisBooker()
            try:
                # Attempt to book
                if booker.setup_driver() and booker.login(user_data['email'], user_data['password']):
                    try:
                        success = booker.book_court(
                            court_number,
                            booking_date,
                            preferred_time
                        )
                        
                        if success:
                            used_accounts.append(username)
                            logging.info(f"[MANUAL] SUCCESS: Booked court {court_number} at {preferred_time} with {username}")
                        else:
                            logging.warning(f"[MANUAL] FAILED: Could not book court {court_number} at {preferred_time} with {username}")
                    except Exception as e:
                        logging.error(f"[MANUAL] ERROR during booking with {username}: {str(e)}")
            except Exception as e:
                logging.error(f"[MANUAL] ERROR with session for {username}: {str(e)}")
            finally:
                try:
                    booker.close()
                except:
                    pass
                
            # Explicitly log that we're moving to the next priority
            logging.info(f"[MANUAL] Moving to next priority court and account...")
        
        # Log summary
        logging.info(f"[MANUAL] Booking complete for {booking_date.strftime('%m/%d/%Y')} - Used accounts: {used_accounts}")

if __name__ == "__main__":
    main() 