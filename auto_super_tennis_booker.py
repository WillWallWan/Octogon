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

# Set up logging with more detailed format and separate levels for handlers
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)  # Set root logger to lowest level

# File Handler - logs everything DEBUG and above
file_handler = logging.FileHandler('tennis_booker.log') # Consider changing log file name
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)

# Console Handler - logs only INFO and above
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO) # Only show INFO, WARNING, ERROR, CRITICAL on console
root_logger.addHandler(console_handler)

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
        # Store details for logging in submit method if needed
        self.court_info_for_logging = "Unknown"
        self.setup_driver()

    def setup_driver(self):
        """Initialize the Chrome WebDriver."""
        try:
            logging.debug("Attempting to initialize Chrome Service...")
            service = Service()
            logging.debug("Chrome Service initialized. Attempting to launch Chrome browser...")
            # Consider adding options to run headless or manage logs
            # options = webdriver.ChromeOptions()
            # options.add_argument("--headless")
            self.driver = webdriver.Chrome(service=service)
            logging.debug("Chrome browser launched. Setting up WebDriverWait...")
            self.wait = WebDriverWait(self.driver, 10)
            logging.debug("WebDriverWait set. Setting implicit wait...")
            self.driver.implicitly_wait(3)  # Reduced wait time
            logging.info("Chrome WebDriver initialized successfully") # Changed to info for more visibility
            return True
        except WebDriverException as e:
            logging.error(f"Failed to initialize WebDriver: {str(e)}")
            return False

    def login(self, email, password):
        """Log in to the tennis reservation system using the existing driver."""
        try:
            # Use the existing driver instance
            if not self.driver:
                logging.error("Driver not initialized before login attempt.")
                return False

            logging.debug(f"[{email}] Attempting to navigate to login page")
            self.driver.get("https://rioc.civicpermits.com/")

            # Find the email and password fields and fill them directly
            logging.debug(f"[{email}] Filling login credentials")
            self.wait.until(EC.element_to_be_clickable((By.ID, "loginEmail"))).send_keys(email)
            self.wait.until(EC.element_to_be_clickable((By.ID, "loginPassword"))).send_keys(password)

            # Click the login button
            logging.debug(f"[{email}] Clicking login button")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//form[@id="login"]/div/table/tbody/tr/td/button'))).click()

            # Wait for the login to complete by checking for a known element on the dashboard
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//a[@href="/Permits/New" and @class="button"]')) # 'New Permit' button
                )
                logging.info(f"Successfully logged in as {email}")
                return True
            except TimeoutException:
                logging.error(f"Login failed for {email}: Did not reach dashboard after login click.")
                return False

        except Exception as e:
            logging.error(f"Login failed for {email}: {str(e)}")
            return False

    def check_availability(self): # Currently unused but kept for potential future use
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
            return True

    def start_new_permit_form(self):
        """Start a new permit form."""
        logging.debug("Navigating to new permit form")
        
        # More robust approach to handle the overlay issue
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # First wait for any existing overlay to disappear
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.blockUI.blockOverlay"))
                    )
                except TimeoutException:
                    logging.debug(f"Attempt {attempt+1}/{max_attempts}: Overlay not present or did not disappear in 10s.")
                
                # Then wait until the button is clickable
                new_permit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[@href="/Permits/New" and @class="button"]'))
                )
                
                # Try JavaScript click which can sometimes bypass overlay issues
                self.driver.execute_script("arguments[0].click();", new_permit_button)
                
                # If we reach here without exception, break the loop
                logging.debug("Successfully clicked New Permit button")
                break
                
            except Exception as e:
                if attempt < max_attempts - 1:  # If not the last attempt
                    logging.warning(f"Attempt {attempt+1}/{max_attempts} to click New Permit button failed: {str(e)}. Retrying...")
                    time.sleep(2)  # Add a short delay before retrying
                else:
                    # On last attempt, re-raise the exception
                    logging.error(f"All {max_attempts} attempts to click New Permit button failed.")
                    raise
        
        logging.debug("Filling activity field")
        self.wait.until(EC.element_to_be_clickable((By.ID, "activity"))).send_keys("Tennis Match")

    def select_court(self, court_number):
        """Select a specific court from the list."""
        logging.debug(f"Selecting court {court_number}")
        if court_number not in COURT_IDS:
            raise ValueError(f"Unknown court number: {court_number}")

        try:
            # Determine court name
            if court_number in (1, 4, 5, 6):
                court_name = f"Octagon Tennis Court {court_number}"
            elif court_number in (2, 3):
                court_name = f"Octagon Tennis court {court_number}"
            else:
                raise ValueError(f"Unknown court number: {court_number}")

            # Select the site from dropdown
            site_dropdown = Select(self.wait.until(EC.element_to_be_clickable((By.ID, "site"))))
            site_dropdown.select_by_visible_text(court_name)
            time.sleep(1) # Allow facility list to update

            # Click "Add Facility" button
            logging.debug("Clicking Add Facility button")
            add_facility_button = self.wait.until(EC.element_to_be_clickable((By.ID, "addFacilitySet")))
            self.driver.execute_script("arguments[0].click();", add_facility_button)

            # Select the specific facility checkbox
            checkbox_id = COURT_IDS[court_number]
            facility_checkbox = self.wait.until(EC.element_to_be_clickable((By.ID, checkbox_id)))
            if not facility_checkbox.is_selected():
                facility_checkbox.click()

        except NoSuchElementException as e:
            logging.error(f"Court {court_number} element not found: {str(e)}")
            raise CourtUnavailableError(f"Court {court_number} is not available or element ID changed")
        except Exception as e:
            logging.error(f"Error selecting court {court_number}: {str(e)}")
            raise

    def set_date_and_time(self, booking_date, start_time):
        """Set the date and time on the form."""
        formatted_date = booking_date.strftime('%m/%d/%Y')
        logging.debug(f"Setting date to {formatted_date}")
        date_field = self.wait.until(EC.element_to_be_clickable((By.ID, "event0")))
        date_field.send_keys(formatted_date)
        self.driver.find_element(By.TAG_NAME, 'body').click() # Trigger validation
        logging.debug("Waiting briefly after setting date...")
        time.sleep(0.5) # Short pause after date setting

        start_hour = int(start_time.split(':')[0])
        end_hour = start_hour + 1
        logging.info(f"Setting time to {start_hour}:00-{end_hour}:00")

        try:
            start_hour_dropdown = Select(self.wait.until(EC.element_to_be_clickable((By.NAME, "startHour"))))
            start_hour_dropdown.select_by_value(str(start_hour))
            end_hour_dropdown = Select(self.wait.until(EC.element_to_be_clickable((By.NAME, "endHour"))))
            end_hour_dropdown.select_by_value(str(end_hour))
            time.sleep(0.2)
        except Exception as e:
            logging.error(f"Error setting time: {str(e)}")
            raise

    def _fill_permit_questions(self):
        """Fill out the permit questions section."""
        logging.debug("Filling permit questions")
        try:
            # Using IDs directly
            self.wait.until(EC.element_to_be_clickable((By.ID, "11e79e5d3daf4712b9e6418d2691b976"))).send_keys("Playing tennis")
            self.wait.until(EC.element_to_be_clickable((By.ID, "af8966101be44676b4ee564b052e1e87"))).send_keys("2")
            self.wait.until(EC.element_to_be_clickable((By.ID, "f28f0dbea8b5438495778b0bb0ddcd93"))).send_keys("No")
            self.wait.until(EC.element_to_be_clickable((By.ID, "d46cb434558845fb9e0318ab6832e427"))).send_keys("No")
            self.wait.until(EC.element_to_be_clickable((By.ID, "1221940f5cca4abdb5288cfcbe284820"))).send_keys("None")
            self.wait.until(EC.element_to_be_clickable((By.ID, "0ce54956c4b14746ae5d364507da1e85"))).send_keys("None")
            self.wait.until(EC.element_to_be_clickable((By.ID, "6b1dda4172f840c7879662bcab1819db"))).send_keys("None")
            self.wait.until(EC.element_to_be_clickable((By.ID, "a31f4297075e4dab8c0ef154f2b9b1c1"))).send_keys("None")

            # Dropdowns
            Select(self.wait.until(EC.element_to_be_clickable((By.ID, "3754dcef7216446b9cc4bf1cd0f12a2e")))).select_by_visible_text("No")
            Select(self.wait.until(EC.element_to_be_clickable((By.ID, "06b3f73192a84fd6b88758e56a64c3ad")))).select_by_visible_text("No")

            # Terms checkbox
            self.wait.until(EC.element_to_be_clickable((By.ID, "acceptTerms"))).click()
            time.sleep(0.2)
            logging.debug("Successfully filled permit questions")

        except Exception as e:
            logging.error(f"Failed to fill permit questions: {str(e)}")
            raise

    def prepare_booking(self, court_number, booking_date, start_time):
        """Prepare the booking form up to the point before final submission click."""
        # Store details for logging in the submit method
        self.court_info_for_logging = f"Court {court_number} on {booking_date.strftime('%m/%d/%Y')} at {start_time}"
        try:
            self.start_new_permit_form()
            self.select_court(court_number)
            self.set_date_and_time(booking_date, start_time)

            logging.info(f"Continuing to permit questions page for {self.court_info_for_logging}")
            continue_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".controlArea button")))
            continue_button.click()
            time.sleep(2) # Wait for questions page to load

            self._fill_permit_questions()

            logging.debug("Scrolling to bottom of the page.")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.2)

            logging.info(f"Booking preparation complete for {self.court_info_for_logging}. Ready for timed submission.")
            return True

        except CourtUnavailableError as e:
            # Log as warning because this might be expected (court taken during prep)
            logging.warning(f"Preparation failed for {self.court_info_for_logging}: {str(e)}")
            return False
        except Exception as e:
            # Log other exceptions during preparation as errors
            logging.error(f"Failed to prepare booking for {self.court_info_for_logging}: {str(e)}")
            try:
                logging.debug(f"Current URL during preparation error: {self.driver.current_url}")
            except Exception: # Handle cases where driver might be dead
                pass 
            return False

    def submit_prepared_booking(self):
        """Finds and clicks the final submit button. No result checking."""
        if not self.driver:
            logging.warning(f"Attempted to click submit for {self.court_info_for_logging}, but driver was already closed.")
            return # Cannot proceed
            
        logging.info(f"Clicking final submit button for {self.court_info_for_logging}")
        try:
            # Find the button
            submit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@id='cancelNewPermitRequest']/preceding-sibling::button"))
            )
            # Click using JavaScript
            self.driver.execute_script("arguments[0].click();", submit_button)
            logging.info(f"Submit button clicked via JS for {self.court_info_for_logging}. No result check performed.")
            # NO time.sleep() here
            # NO result checking here

        except TimeoutException:
             # Log error if button wasn't clickable in time
             logging.error(f"Error clicking submit for {self.court_info_for_logging}: Submit button not found or clickable in time.")
        except Exception as e:
            # Log any other errors during the find/click process
            logging.error(f"Error clicking submit for {self.court_info_for_logging}: {str(e)}")
            # Note: We don't return True/False as we aren't checking success

    def close(self):
        """Close the browser."""
        if self.driver:
            logging.debug(f"Closing browser window ({self.court_info_for_logging}).")
            try:
                self.driver.quit()
            except Exception as e:
                 logging.error(f"Error quitting driver ({self.court_info_for_logging}): {e}")
            self.driver = None # Prevent reuse

def main():
    """Main function to prepare and automatically submit tennis court bookings at 8 AM."""
    # --- Configuration --- 
    SUBMIT_HOUR = 8
    SUBMIT_MINUTE = 0
    SUBMIT_SECOND = 9 # Aim slightly before if needed? e.g., 59
    # Optional: Add a small random delay before each submission click to reduce load?
    # SUBMIT_DELAY_MAX_SECONDS = 0.5 

    # --- Initialization --- 
    prepared_instances = [] # List to hold booker instances ready for submission
    accounts = list(USERS.keys())
    random.shuffle(accounts)
    account_index = 0

    # --- Determine Target Booking Dates --- 
    today_weekday = datetime.now().weekday()
    days_ahead_to_book = BOOKING_RULES.get(today_weekday, [])

    if not days_ahead_to_book:
        logging.info(f"No booking rules defined for today (weekday {today_weekday}). Exiting.")
        return

    logging.info(f"Today is {datetime.now():%A}. Booking rules active: {days_ahead_to_book} days ahead.")

    # Log the planned court bookings based on priorities
    priority_log = "Planning to prepare bookings based on COURT_PRIORITIES:\n"
    for i, p in enumerate(COURT_PRIORITIES):
        priority_log += f"  Priority {i+1}: Court {p['court']} at {p['time']}\n"
    logging.info(priority_log.strip()) # Use strip() to remove trailing newline

    # Log the configured submission time
    logging.info(f"Configured target submission time: {SUBMIT_HOUR:02d}:{SUBMIT_MINUTE:02d}:{SUBMIT_SECOND:02d}")

    # --- Preparation Phase --- 
    logging.info("--- Starting Preparation Phase ---")
    for days_ahead in days_ahead_to_book:
        # Ensure booking_date is a date object first, then format where needed
        booking_date_obj = datetime.now().date() + timedelta(days=days_ahead)
        logging.info(f"== Preparing bookings for {booking_date_obj.strftime('%A, %m/%d/%Y')} ({days_ahead} days ahead) ==")

        # Process each priority for this date
        for i, priority in enumerate(COURT_PRIORITIES):
            if account_index >= len(accounts):
                logging.warning(f"No more accounts available. Stopping preparation for {booking_date_obj.strftime('%m/%d/%Y')}.")
                break # Stop processing priorities for this date if out of accounts

            # Get the next account
            username = accounts[account_index]
            user_data = USERS[username]
            court_number = priority["court"]
            preferred_time = priority["time"]
            logging.info(f"Priority #{i+1}: Assigning {username} to prepare Court {court_number} at {preferred_time} for {booking_date_obj.strftime('%m/%d/%Y')}")

            booker = TennisBooker()
            try:
                if booker.driver and booker.login(user_data['email'], user_data['password']):
                    # Pass the date object to prepare_booking
                    preparation_success = booker.prepare_booking(
                        court_number,
                        booking_date_obj, 
                        preferred_time
                    )

                    if preparation_success:
                        prepared_instances.append(booker) # Keep instance open
                        account_index += 1 # Only increment if successfully prepared
                    else:
                        # If preparation failed (e.g., court unavailable), close this browser
                        logging.warning(f"Closing browser for {username} due to failed preparation for {booker.court_info_for_logging}.")
                        booker.close()
                else:
                    # Handle setup_driver failure or login failure
                    logging.warning(f"Skipping preparation for {username} due to setup/login failure. Closing browser.")
                    booker.close()

            except Exception as e:
                # Catch unexpected errors during the whole prep attempt for one user
                logging.error(f"UNEXPECTED ERROR during preparation attempt for {username}: {str(e)}. Closing browser.")
                try:
                    booker.close()
                except Exception as close_err:
                    logging.error(f"Error closing browser after unexpected error for {username}: {close_err}")

        logging.info(f"== Finished preparation attempts for {booking_date_obj.strftime('%m/%d/%Y')} ==")

    # --- End Preparation Phase ---

    if not prepared_instances:
        logging.info("No bookings were successfully prepared. Exiting.")
        return

    logging.info(f"--- Preparation Complete: {len(prepared_instances)} instances ready for submission ---")

    # --- Waiting Phase --- 
    now = datetime.now()
    # Calculate target time based on today's date
    target_submit_time = now.replace(hour=SUBMIT_HOUR, minute=SUBMIT_MINUTE, second=SUBMIT_SECOND, microsecond=0)

    # If target time is in the past for today, set it for tomorrow
    if now >= target_submit_time:
        logging.info(f"Target submit time {target_submit_time.strftime('%H:%M:%S')} has passed for today. Setting target for tomorrow.")
        target_submit_time += timedelta(days=1)

    wait_seconds = (target_submit_time - now).total_seconds()

    if wait_seconds > 0:
        logging.info(f"Waiting for {wait_seconds:.2f} seconds until target submission time: {target_submit_time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(wait_seconds)
    else:
        # This case should ideally not happen if run before 8 AM, but handles running it after.
         logging.info("Target submission time is now or in the past. Proceeding immediately.")

    # --- Submission Phase --- 
    logging.info(f"--- Target time reached! Starting RAPID Submission Phase at {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')} ---")
    submit_attempts = 0
    submit_errors = 0
    
    # Loop 1: Click Submit on all prepared instances with staggering
    logging.info("--- Clicking Submit on all instances (Phase 1) with staggering ---")
    for idx, booker_instance in enumerate(prepared_instances):
        logging.info(f"Clicking submit for instance {idx+1}/{len(prepared_instances)} ({booker_instance.court_info_for_logging})")
        try:
            # Optional: Add tiny random sleep *before* clicking if desired
            # time.sleep(random.uniform(0, 0.1)) 
            booker_instance.submit_prepared_booking() # Click submit
            submit_attempts += 1

            # Staggering logic: Pause for 1 second after every 3rd submission, 
            # but not after the very last one.
            if (idx + 1) % 3 == 0 and (idx + 1) < len(prepared_instances):
                logging.info(f"Pausing for 1 second after submitting batch ending with instance {idx+1}...")
                time.sleep(1) 
            # NO close() here
        except Exception as submit_err:
            # Log if the submit method itself had an unexpected error
            logging.error(f"Unexpected error during submit click for {booker_instance.court_info_for_logging}: {submit_err}")
            submit_errors += 1

    logging.info(f"--- Submit Clicking Phase Complete: {submit_attempts}/{len(prepared_instances)} submit clicks attempted. Submit errors: {submit_errors} ---")

    # Add a pause AFTER all clicks before closing, to allow submissions to register
    # Adjust the sleep duration as needed
    close_delay_seconds = 5 
    logging.info(f"Waiting {close_delay_seconds} seconds before closing browser windows...")
    time.sleep(close_delay_seconds) 

    # --- Cleanup Phase ---
    logging.info("--- Starting Cleanup Phase (Closing all browser windows - Phase 2) ---")
    closed_count = 0
    close_errors = 0
    # Loop 2: Close all instances
    for idx, booker_instance in enumerate(prepared_instances):
        logging.info(f"Closing instance {idx+1}/{len(prepared_instances)} ({booker_instance.court_info_for_logging})")
        try:
            booker_instance.close()
            closed_count += 1
        except Exception as close_err:
            logging.error(f"Error closing browser window ({booker_instance.court_info_for_logging}): {close_err}")
            close_errors += 1

    logging.info(f"--- Cleanup Phase Complete: {closed_count}/{len(prepared_instances)} windows closed. Close errors: {close_errors} ---")
    logging.info("--- Script finished. ---")
    # No final summary of success/failure, as results were not checked.

if __name__ == "__main__":
    main() 