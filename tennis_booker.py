import time
import logging
import random
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, ElementNotInteractableException
from config import USERS, BOOKING_WINDOW_START, BOOKING_WINDOW_END, COURT_IDS, BOOKING_RULES, COURT_PRIORITIES

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level for more information
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('tennis_booker.log'),
        logging.StreamHandler()
    ]
)

# Set to True for debugging with longer pauses
DEBUG_MODE = False
success_delay = 5 if DEBUG_MODE else 2

# WebDriver paths
CHROME_DRIVER_PATH = "/Users/willwallwan/chromedriver"  # Update with actual path

# Tennis court booking URL
TENNIS_URL = "https://roosevelt.perfectmind.com/24063/Menu/BookMe4LandingPages?widgetId=15f6af07-39c5-473e-b053-96653f77a406&redirectedFromEmbededMode=False&categoryId=4e7bbe4a-07a7-474f-a6f8-2f46eaa14631"

class CourtUnavailableError(Exception):
    """Custom exception for when a court is unavailable."""
    pass

class TennisBooker:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.setup_driver()

    def setup_driver(self):
        """Initialize the Chrome WebDriver."""
        try:
            service = Service()
            self.driver = webdriver.Chrome(service=service)
            self.wait = WebDriverWait(self.driver, 10)
            self.driver.implicitly_wait(3)  # Reduced wait time
            logging.debug("Chrome WebDriver initialized successfully")
            return True
        except WebDriverException as e:
            logging.error(f"Failed to initialize WebDriver: {str(e)}")
            return False

    def login(self, email, password):
        """Log in to the tennis reservation system."""
        try:
            # Create a new browser instance for login
            service = Service()
            driver = webdriver.Chrome(service=service)
            driver.implicitly_wait(3)  # Reduced wait time
            
            logging.debug("Attempting to navigate to login page")
            driver.get("https://rioc.civicpermits.com/")
            
            # Find the email and password fields and fill them directly like in Octogon.py
            logging.debug("Filling login credentials")
            driver.find_element(By.ID, "loginEmail").send_keys(email)
            driver.find_element(By.ID, "loginPassword").send_keys(password)
            
            # Click the login button - match Octogon.py's approach
            logging.debug("Clicking login button")
            driver.find_element(By.XPATH, '//form[@id="login"]/div/table/tbody/tr/td/button').click()
            
            # Wait for the login to complete
            time.sleep(0.5)
            
            # Update the main driver with the logged-in session
            self.driver = driver
            self.wait = WebDriverWait(self.driver, 10)
            
            logging.info(f"Successfully logged in as {email}")
            return True
            
        except Exception as e:
            logging.error(f"Login failed for {email}: {str(e)}")
            if 'driver' in locals():
                driver.quit()
            return False

    def check_availability(self):
        """Check if there are any availability error messages."""
        try:
            # Look for the specific error message
            error_messages = self.driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .alert-error, .validation-summary-errors")
            for error in error_messages:
                if "The selected facilities are not available for the above date and time." in error.text:
                    logging.info("Court is already booked for this time slot")
                    return False
            return True
        except Exception as e:
            logging.error(f"Error checking availability: {str(e)}")
            return True  # Default to true to allow the booking attempt to continue

    def start_new_permit_form(self):
        """Start a new permit form."""
        logging.debug("Starting new permit form")
        
        # Wait for the New Permit button exactly like in Octogon.py
        WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@href="/Permits/New" and @class="button"]'))
        ).click()
        
        # Fill activity field exactly like in Octogon.py
        self.wait.until(EC.element_to_be_clickable((By.ID, "activity"))).send_keys("Tennis Match")

    def select_court(self, court_number):
        """Select a specific court from the list."""
        logging.debug(f"Selecting court {court_number}")
        
        # Check that the court number is valid
        if court_number not in COURT_IDS:
            raise ValueError(f"Unknown court number: {court_number}")
        
        try:
            # Determine court name just like in Octogon.py
            if court_number in (1, 4, 5, 6):
                court_name = f"Octagon Tennis Court {court_number}"
            elif court_number in (2, 3):
                court_name = f"Octagon Tennis court {court_number}"
            else:
                raise ValueError(f"Unknown court number: {court_number}")
            
            # First select the site from dropdown (exactly like Octogon.py)
            site_dropdown = Select(self.wait.until(EC.element_to_be_clickable((By.ID, "site"))))
            site_dropdown.select_by_visible_text(court_name)
            
            # Add a small wait like in Octogon.py
            time.sleep(1)
            
            logging.debug("Clicking Add Facility button")
            # Click "Add Facility" button like in Octogon.py
            add_facility_button = self.wait.until(EC.element_to_be_clickable((By.ID, "addFacilitySet")))
            self.driver.execute_script("arguments[0].click();", add_facility_button)
            
            # Select the facility checkbox using the court ID
            checkbox_id = COURT_IDS[court_number]
            facility_checkbox = self.wait.until(EC.element_to_be_clickable((By.ID, checkbox_id)))
            if not facility_checkbox.is_selected():
                facility_checkbox.click()
            
        except NoSuchElementException as e:
            logging.error(f"Court {court_number} was not found on the page: {str(e)}")
            raise CourtUnavailableError(f"Court {court_number} is not available")
        except Exception as e:
            logging.error(f"Error selecting court {court_number}: {str(e)}")
            raise

    def set_date_and_time(self, booking_date, start_time):
        """Set the date and time on the form."""
        # Format the date string
        formatted_date = booking_date.strftime('%m/%d/%Y')
        logging.debug(f"Setting date to {formatted_date}")
        
        # Set the date directly exactly like in Octogon.py
        date_field = self.wait.until(EC.element_to_be_clickable((By.ID, "event0")))
        date_field.send_keys(formatted_date)

        # Click body to trigger date validation 
        self.driver.find_element(By.TAG_NAME, 'body').click()

        # Add a flat delay instead of checking availability
        logging.debug("Waiting for date validation...")
        # time.sleep(1)
        
        # Comment out availability check
        # if not self.check_availability():
        #     raise CourtUnavailableError(f"Court is not available on {formatted_date}")
            
        # Extract hour from time string (e.g., "18:00" → 18)
        start_hour = int(start_time.split(':')[0])
        end_hour = start_hour + 1
        
        logging.info(f"Setting time to {start_hour}:00-{end_hour}:00")
        
        try:
            # Use the exact same approach as Octogon.py
            start_hour_dropdown = Select(self.wait.until(EC.element_to_be_clickable((By.NAME, "startHour"))))
            start_hour_dropdown.select_by_value(str(start_hour))
            
            end_hour_dropdown = Select(self.wait.until(EC.element_to_be_clickable((By.NAME, "endHour"))))
            end_hour_dropdown.select_by_value(str(end_hour))
            
            time.sleep(0.2)
        except Exception as e:
            logging.error(f"Error setting time: {str(e)}")
            raise

        # Comment out second availability check
        # if not self.check_availability():
        #     raise CourtUnavailableError(f"Court is not available at {start_time}")

    def book_court(self, court_number, booking_date, start_time, success_delay=5):
        """Attempt to book a court for the given date and time."""
        try:
            # Start a new form
            self.start_new_permit_form()
            
            # Select the court
            self.select_court(court_number)
            
            # Set date and time
            self.set_date_and_time(booking_date, start_time)
            
            logging.info(f"Attempting to book court {court_number} for {booking_date.strftime('%m/%d/%Y')} at {start_time}")
            
            # Click Continue - exact same approach as Octogon.py
            continue_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".controlArea button")))
            continue_button.click()
            time.sleep(2)  # Match Octogon.py timing

            # Fill in permit questions
            self._fill_permit_questions()

            # Submit the request using exact same approach as Octogon.py
            try:
                submit_button = self.driver.find_element(
                    By.XPATH, "//button[@id='cancelNewPermitRequest']/preceding-sibling::button"
                )
                
                # Scroll to the button then click using JavaScript like in Octogon.py
                self.driver.execute_script("arguments[0].scrollIntoView();", submit_button)
                time.sleep(0.2)  # Match Octogon.py timing
                
                # Click the button using JavaScript like in Octogon.py
                self.driver.execute_script("arguments[0].click();", submit_button)
                logging.info(f"Submitted request for court {court_number}")
                
                # Wait a bit longer for submission to complete
                time.sleep(2)
                
                # Check for success or errors
                success_elements = self.driver.find_elements(By.CSS_SELECTOR, ".alert-success")
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .alert-error, .validation-summary-errors")
                
                if success_elements:
                    logging.info(f"Successfully booked court {court_number} for {booking_date.strftime('%m/%d/%Y')} at {start_time}")
                    time.sleep(success_delay)  # Keep browser open to verify success
                    return True
                elif error_elements:
                    for error in error_elements:
                        logging.error(f"Booking error: {error.text}")
                    return False
                else:
                    logging.warning("No success or error messages found after submission")
                    return False
                
            except Exception as e:
                logging.error(f"Error finding or clicking the submit button: {str(e)}")
                return False

        except CourtUnavailableError as e:
            logging.info(str(e))
            return False
        except Exception as e:
            logging.error(f"Failed to book court {court_number}: {str(e)}")
            logging.debug(f"Current URL: {self.driver.current_url}")
            return False

    def _fill_permit_questions(self):
        """Fill out the permit questions section like in Octogon.py."""
        try:
            # Fill in all fields directly like in Octogon.py with minimal waits
            self.wait.until(EC.element_to_be_clickable((By.ID, "11e79e5d3daf4712b9e6418d2691b976"))).send_keys("Playing tennis")
            self.wait.until(EC.element_to_be_clickable((By.ID, "af8966101be44676b4ee564b052e1e87"))).send_keys("2")
            self.wait.until(EC.element_to_be_clickable((By.ID, "f28f0dbea8b5438495778b0bb0ddcd93"))).send_keys("No")
            self.wait.until(EC.element_to_be_clickable((By.ID, "d46cb434558845fb9e0318ab6832e427"))).send_keys("No")
            self.wait.until(EC.element_to_be_clickable((By.ID, "1221940f5cca4abdb5288cfcbe284820"))).send_keys("None")
            self.wait.until(EC.element_to_be_clickable((By.ID, "0ce54956c4b14746ae5d364507da1e85"))).send_keys("None")
            self.wait.until(EC.element_to_be_clickable((By.ID, "6b1dda4172f840c7879662bcab1819db"))).send_keys("None")
            self.wait.until(EC.element_to_be_clickable((By.ID, "a31f4297075e4dab8c0ef154f2b9b1c1"))).send_keys("None")

            # Select dropdowns like in Octogon.py
            previous_permit_dropdown = Select(self.wait.until(EC.element_to_be_clickable((By.ID, "3754dcef7216446b9cc4bf1cd0f12a2e"))))
            previous_permit_dropdown.select_by_visible_text("No")

            security_dropdown = Select(self.wait.until(EC.element_to_be_clickable((By.ID, "06b3f73192a84fd6b88758e56a64c3ad"))))
            security_dropdown.select_by_visible_text("No")

            # Click terms checkbox directly like in Octogon.py
            self.wait.until(EC.element_to_be_clickable((By.ID, "acceptTerms"))).click()
            time.sleep(0.2)  # Match Octogon.py timing
                
            logging.debug("Successfully filled permit questions")
            
        except Exception as e:
            logging.error(f"Failed to fill permit questions: {str(e)}")
            raise

    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()

def is_valid_booking_time():
    """Check if current time is within valid booking window."""
    # TEMPORARY OVERRIDE FOR TESTING - REMOVE LATER
    return True
    
    now = datetime.now()
    start_time = datetime.strptime(BOOKING_WINDOW_START, "%H:%M").time()
    end_time = datetime.strptime(BOOKING_WINDOW_END, "%H:%M").time()
    
    # Check if it's a weekday
    if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        logging.info("Cannot book on weekends")
        return False
    
    # Check if current time is within booking window
    if not (start_time <= now.time() <= end_time):
        logging.info("Current time is outside booking window")
        return False
    
    return True

def main():
    """Main function to run the tennis court booking system with simplified court/account assignment."""
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
        logging.info(f"Attempting to book for {booking_date.strftime('%A, %m/%d/%Y')} ({days_ahead} days ahead)")
        
        # Get list of available accounts and shuffle them
        accounts = list(USERS.keys())
        random.shuffle(accounts)
        
        # Keep track of which accounts we've used
        used_accounts = []
        
        # Process each priority with a different account
        for i, priority in enumerate(COURT_PRIORITIES):
            # Check if we have any accounts left
            if i >= len(accounts):
                logging.warning(f"No more accounts available for priority #{i+1}")
                break
                
            # Get the next account
            username = accounts[i]
            user_data = USERS[username]
            
            # Get court and time from priority
            court_number = priority["court"]
            preferred_time = priority["time"]
            
            logging.info(f"Priority #{i+1}: Assigning {username} to book court {court_number} at {preferred_time}")
            
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
                            logging.info(f"SUCCESS: Booked court {court_number} at {preferred_time} with {username}")
                        else:
                            logging.warning(f"FAILED: Could not book court {court_number} at {preferred_time} with {username}")
                    except Exception as e:
                        logging.error(f"ERROR during booking with {username}: {str(e)}")
            except Exception as e:
                logging.error(f"ERROR with session for {username}: {str(e)}")
            finally:
                try:
                    booker.close()
                except:
                    pass
                
            # Explicitly log that we're moving to the next priority
            logging.info(f"Moving to next priority court and account...")
        
        # Log summary
        logging.info(f"Booking complete for {booking_date.strftime('%m/%d/%Y')} - Used accounts: {used_accounts}")

if __name__ == "__main__":
    main() 