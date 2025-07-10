import time
import logging
import random
import os
import socket
import threading
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException
from config import USERS, BOOKING_WINDOW_START, BOOKING_WINDOW_END, COURT_IDS, BOOKING_RULES, COURT_PRIORITIES
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import OperationSystemManager
import sys
import subprocess
import urllib.request, zipfile, tempfile, shutil
from pathlib import Path

# Set up logging with more detailed format and separate levels for handlers
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)  # Set root logger to lowest level

# Action Log Handler (INFO from script, INFO+ from Selenium)
action_log_handler = logging.FileHandler('auto_booker_action.log')
action_log_handler.setFormatter(log_formatter)
action_log_handler.setLevel(logging.INFO) # This handler will primarily show INFO and above
# We will add a custom filter to it later to refine what it shows from Selenium vs. our script
root_logger.addHandler(action_log_handler)

# Detailed Debug Log Handler (DEBUG from everything)
debug_log_handler = logging.FileHandler('auto_booker_detailed_debug.log')
debug_log_handler.setFormatter(log_formatter)
debug_log_handler.setLevel(logging.DEBUG) # This handler gets all DEBUG messages
root_logger.addHandler(debug_log_handler)

# Console Handler - logs only INFO and above
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO) # Only show INFO, WARNING, ERROR, CRITICAL on console
root_logger.addHandler(console_handler)

# Reduce verbosity of Selenium loggers to make the log file cleaner
# The global Selenium logger level changes are removed; filtering will be per-handler.

# Set to True for debugging with longer pauses
DEBUG_MODE = False
success_delay = 5 if DEBUG_MODE else 2

# WebDriver paths are now managed automatically by webdriver-manager
# CHROME_DRIVER_PATH = "/Users/willwallwan/chromedriver"  # No longer needed

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
            logging.debug("Attempting to initialize Chrome Service with webdriver-manager...")
            # Resolve local Chrome version so we can fetch an exact-match driver (patch version too).
            def _detect_chrome_version():
                """Return installed Chrome full version without launching the app (macOS only)."""
                if sys.platform != "darwin":
                    return None
                plist = "/Applications/Google Chrome.app/Contents/Info.plist"
                if not os.path.exists(plist):
                    return None
                try:
                    out = subprocess.check_output([
                        "/usr/libexec/PlistBuddy",
                        "-c",
                        "Print :CFBundleShortVersionString",
                        plist,
                    ], text=True)
                    return out.strip()
                except Exception as e:
                    logging.debug(f"Could not determine Chrome version: {e}")
                    return None

            chrome_version = _detect_chrome_version()

            if chrome_version:
                logging.debug(f"Detected Chrome version: {chrome_version}. Fetching matching driver…")
                driver_path = ChromeDriverManager(driver_version=chrome_version).install()
            else:
                logging.debug("Chrome version could not be detected; falling back to latest driver.")
                driver_path = ChromeDriverManager().install()

            # macOS Gatekeeper quarantines downloaded executables; if the attribute is present
            # the chromedriver process will be killed (exit code -9) as soon as it launches.
            # Clearing the attribute once per download makes every future launch safe.
            if sys.platform == "darwin":
                for target in (driver_path, os.path.dirname(driver_path)):
                    if os.path.exists(target):
                        try:
                            subprocess.run(["xattr", "-dr", "com.apple.quarantine", target], check=False)
                        except Exception as e:
                            logging.debug(f"Unable to clear quarantine attribute on {target}: {e}")

            def _launch_with(driver_path):
                """Attempt to create a Chrome Service + WebDriver for the given path."""
                service_obj = Service(driver_path)
                opts = webdriver.ChromeOptions()
                # opts.add_argument("--headless=new")  # keep disabled for visibility
                opts.add_argument("--no-sandbox")
                opts.add_argument("--disable-dev-shm-usage")
                opts.add_argument("--disable-gpu")
                opts.add_argument("--remote-allow-origins=*")
                return webdriver.Chrome(service=service_obj, options=opts)

            # First launch attempt with version-matched driver; if it immediately exits with
            # status –9 fall back to the latest patch available for the same major release.
            try:
                logging.debug("Launching Chrome browser with configured options (exact patch)…")
                self.driver = _launch_with(driver_path)
            except WebDriverException as e:
                if "Status code was: -9" in str(e):
                    logging.warning("Exact-match driver crashed (status –9). Fetching latest patch and retrying…")
                    # Download latest patch (webdriver-manager default) and clear quarantine again
                    driver_path_latest = ChromeDriverManager().install()
                    if sys.platform == "darwin":
                        for target in (driver_path_latest, os.path.dirname(driver_path_latest)):
                            if os.path.exists(target):
                                subprocess.run(["xattr", "-dr", "com.apple.quarantine", target], check=False)
                    try:
                        # Second attempt with latest arm64 patch
                        self.driver = _launch_with(driver_path_latest)
                    except WebDriverException as e2:
                        if "Status code was: -9" in str(e2):
                            logging.warning("Latest arm64 patch also crashed. Trying x64 driver under Rosetta…")
                            try:
                                tmp_dir = Path(tempfile.mkdtemp(prefix="chromedriver_x64_"))
                                zip_path = tmp_dir / "driver.zip"
                                url = (
                                    f"https://storage.googleapis.com/chrome-for-testing-public/"
                                    f"{chrome_version}/mac-x64/chromedriver-mac-x64.zip"
                                )
                                urllib.request.urlretrieve(url, zip_path)
                                with zipfile.ZipFile(zip_path) as zf:
                                    zf.extractall(tmp_dir)
                                driver_path_x64 = str(next(tmp_dir.glob("**/chromedriver")))
                                # Ensure executable permissions
                                os.chmod(driver_path_x64, 0o755)
                                if sys.platform == "darwin":
                                    for target in (driver_path_x64, os.path.dirname(driver_path_x64)):
                                        if os.path.exists(target):
                                            subprocess.run(["xattr", "-dr", "com.apple.quarantine", target], check=False)
                                # Final attempt with x64 driver under Rosetta
                                self.driver = _launch_with(driver_path_x64)
                            except Exception as e3:
                                logging.error(f"Failed to launch x64 driver via Rosetta: {e3}")
                                raise
                        else:
                            raise
                else:
                    raise
            logging.debug("Chrome browser launched. Setting up WebDriverWait...")
            self.wait = WebDriverWait(self.driver, 10)
            # Set page load timeout to prevent indefinite waiting
            self.driver.set_page_load_timeout(30)  # Set to 30 seconds
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
            time.sleep(1) # Extra small pause before interacting with the first field
            activity_field = self.wait.until(EC.element_to_be_clickable((By.ID, "11e79e5d3daf4712b9e6418d2691b976")))
            activity_field.clear()
            activity_field.send_keys("Playing tennis")
            time.sleep(0.1) # Short pause for stability

            num_people_field = self.wait.until(EC.element_to_be_clickable((By.ID, "af8966101be44676b4ee564b052e1e87")))
            num_people_field.clear()
            num_people_field.send_keys("2")
            time.sleep(0.1) # Short pause for stability

            participants_charged_field = self.wait.until(EC.element_to_be_clickable((By.ID, "f28f0dbea8b5438495778b0bb0ddcd93")))
            participants_charged_field.send_keys("No") # Assuming clear() is not needed if default is different or if send_keys overwrites
            time.sleep(0.1)

            spectators_charged_field = self.wait.until(EC.element_to_be_clickable((By.ID, "d46cb434558845fb9e0318ab6832e427")))
            spectators_charged_field.send_keys("No")
            time.sleep(0.1)

            table_chair_field = self.wait.until(EC.element_to_be_clickable((By.ID, "1221940f5cca4abdb5288cfcbe284820")))
            table_chair_field.send_keys("None")
            time.sleep(0.1)

            live_entertainment_field = self.wait.until(EC.element_to_be_clickable((By.ID, "0ce54956c4b14746ae5d364507da1e85")))
            live_entertainment_field.send_keys("None")
            time.sleep(0.1)

            advertised_field = self.wait.until(EC.element_to_be_clickable((By.ID, "6b1dda4172f840c7879662bcab1819db")))
            advertised_field.send_keys("None")
            time.sleep(0.1)

            parking_needs_field = self.wait.until(EC.element_to_be_clickable((By.ID, "a31f4297075e4dab8c0ef154f2b9b1c1")))
            parking_needs_field.send_keys("None")
            time.sleep(0.1)

            # Dropdowns
            prev_permit_dropdown = Select(self.wait.until(EC.element_to_be_clickable((By.ID, "3754dcef7216446b9cc4bf1cd0f12a2e"))))
            prev_permit_dropdown.select_by_visible_text("No")
            time.sleep(0.1)

            on_site_security_dropdown = Select(self.wait.until(EC.element_to_be_clickable((By.ID, "06b3f73192a84fd6b88758e56a64c3ad"))))
            on_site_security_dropdown.select_by_visible_text("No")
            time.sleep(0.1)

            # Wait for any blocking overlay to disappear, then click the terms checkbox via JS
            max_attempts_terms = 3
            for attempt in range(max_attempts_terms):
                try:
                    # Wait up to 10s for the overlay to be gone
                    WebDriverWait(self.driver, 10).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.blockUI.blockOverlay"))
                    )

                    terms_checkbox = self.wait.until(EC.element_to_be_clickable((By.ID, "acceptTerms")))
                    # Use JavaScript click to minimise interception issues
                    self.driver.execute_script("arguments[0].click();", terms_checkbox)
                    break  # success
                except Exception as e:
                    if attempt < max_attempts_terms - 1:
                        logging.warning(f"Attempt {attempt+1}/{max_attempts_terms} to click acceptTerms failed: {e}. Retrying after short wait...")
                        time.sleep(1)
                    else:
                        logging.error("All attempts to click acceptTerms checkbox failed.")
                        raise

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
            try:
                continue_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".controlArea button")))
                # Click with timeout protection using robust JS click
                logging.debug("Scrolling to and clicking continue button...")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", continue_button)
                time.sleep(0.3) # Brief pause for UI to settle
                self.driver.execute_script("arguments[0].click();", continue_button)

                # Wait for the page to actually load by checking for a known element on the questions page
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.ID, "11e79e5d3daf4712b9e6418d2691b976"))  # First question field ID
                )
            except (TimeoutException, ElementClickInterceptedException) as e:
                logging.error(f"Failed to navigate to questions page for {self.court_info_for_logging}: {type(e).__name__} - {e}")
                # Optional: self.driver.save_screenshot(f"error_questions_page_{self.court_info_for_logging.replace(' ', '_')}.png")
                raise
            except Exception as e:
                logging.error(f"Unexpected error navigating to questions page for {self.court_info_for_logging}: {str(e)}")
                raise # Re-raise to be caught by the main loop

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
                self.save_screenshot_on_error() # Save screenshot
            except Exception: # Handle cases where driver might be dead
                pass 
            return False

    def save_screenshot_on_error(self):
        """Saves a screenshot of the current browser window to a 'screenshots' directory."""
        if not self.driver:
            return # Can't take screenshot if driver is dead

        try:
            # Create screenshots directory if it doesn't exist
            screenshots_dir = os.path.join(os.getcwd(), "screenshots")
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
            
            # Generate a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Sanitize the court info for a valid filename
            sanitized_info = self.court_info_for_logging.replace(' ', '_').replace('/', '-').replace(':', '')
            filename = f"error_{timestamp}_{sanitized_info}.png"
            filepath = os.path.join(screenshots_dir, filename)

            self.driver.save_screenshot(filepath)
            logging.info(f"Saved screenshot of error to: {filepath}")

        except Exception as e:
            logging.error(f"Failed to save screenshot: {e}")

    def keep_alive(self):
        """Perform a simple action to keep the webdriver session alive."""
        if not self.driver:
            return False
        try:
            _ = self.driver.title # Getting title is a lightweight operation
            logging.debug(f"Keep-alive ping successful for {self.court_info_for_logging}")
            return True
        except WebDriverException as e:
            # This is expected if the browser has been closed manually or crashed
            if "invalid session id" in str(e).lower():
                logging.warning(f"Keep-alive ping FAILED for {self.court_info_for_logging}: Session is invalid or browser closed.")
            else:
                logging.warning(f"Keep-alive ping FAILED for {self.court_info_for_logging} with unexpected error: {e}")
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

def check_internet_connection(host="8.8.8.8", port=53, timeout=3, retries=5, delay=15):
    """
    Checks for a live internet connection by attempting to connect to Google's DNS.
    Retries a few times before giving up.
    """
    for i in range(retries):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            logging.info("Internet connection check successful.")
            return True
        except socket.error as ex:
            if i < retries - 1:
                logging.warning(f"Internet connection check failed (Attempt {i+1}/{retries}): {ex}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logging.error(f"Internet connection failed after {retries} attempts. Cannot proceed.")
                return False

def keep_alive_pinger(instances_list, stop_event):
    """
    A background thread function that periodically pings all browser instances
    to keep them from timing out.
    """
    while not stop_event.is_set():
        # Wait for 20 seconds, but check the stop event every second
        for _ in range(20):
            if stop_event.is_set():
                break
            time.sleep(1)
        
        if not stop_event.is_set():
            logging.info(f"HEARTBEAT: Pinging {len(instances_list)} prepared instance(s)...")
            alive_count = 0
            # Iterate over a copy of the list in case it's modified by the main thread
            for inst in list(instances_list):
                if inst.keep_alive():
                    alive_count += 1
            logging.info(f"HEARTBEAT: {alive_count}/{len(instances_list)} instances responded.")

def main():
    """Main function to prepare and automatically submit tennis court bookings at 8 AM."""
    # --- Configuration --- 
    SUBMIT_HOUR = 8
    SUBMIT_MINUTE = 0
    # SUBMIT_SECOND values can now be configured per weekday (0 = Monday ... 6 = Sunday)
    # Feel free to tweak individual seconds as desired – only the values in this
    # dictionary need to be edited.
    SUBMIT_SECOND_BY_DAY = {
        0: 1,  # Monday
        1: 1,  # Tuesday
        2: 1,  # Wednesday
        3: 6,  # Thursday
        4: 6,  # Friday
        # 5 and 6 (Saturday/Sunday) are not normally used but are provided for completeness.
        5: 3,
        6: 3,
    }

    # The script will look up today's weekday; if it is missing from the map we default to 3 s.
    SUBMIT_SECOND = SUBMIT_SECOND_BY_DAY.get(datetime.now().weekday(), 3)

    SUBMIT_DELAY_MAX_SECONDS = 0.5 

    # Max time (in seconds) we allow a single prepare_booking() call to run before
    # we consider it hung and discard the attempt.
    MAX_PREP_TIME_PER_INSTANCE_SECONDS = 90

    # --- Initialization --- 
    prepared_instances = [] # List to hold booker instances ready for submission
    accounts = list(USERS.keys())
    random.shuffle(accounts)
    account_index = 0
    
    # --- Heartbeat Thread Setup ---
    stop_pinger_event = threading.Event()
    pinger_thread = threading.Thread(
        target=keep_alive_pinger,
        args=(prepared_instances, stop_pinger_event),
        daemon=True  # Allow main program to exit without waiting
    )
    pinger_thread.start()

    # --- Determine Target Booking Dates & Actual Submission Time --- 
    now = datetime.now()
    today_weekday = now.weekday()

    # SUBMIT_SECOND has already been set via SUBMIT_SECOND_BY_DAY above.
    # Logging here for clarity.
    logging.debug(f"SUBMIT_SECOND for weekday {today_weekday} set to {SUBMIT_SECOND} s.")

    # Calculate the target_submit_time for today or tomorrow
    target_submit_time = now.replace(hour=SUBMIT_HOUR, minute=SUBMIT_MINUTE, second=SUBMIT_SECOND, microsecond=0)
    if now >= target_submit_time:
        logging.info(f"Configured submit time {target_submit_time.strftime('%H:%M:%S')} has passed for today. Setting target for tomorrow.")
        target_submit_time += timedelta(days=1)
    logging.info(f"Actual target submission time: {target_submit_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # i.e. 30 s before the top of the hour plus today's SUBMIT_SECOND value.
    PREPARATION_CUTOFF_SECONDS_DYNAMIC = 30 + SUBMIT_SECOND  # e.g. 33 s (Mon-Wed) or 37 s (Thu/Fri)
    preparation_hard_stop_time = target_submit_time - timedelta(seconds=PREPARATION_CUTOFF_SECONDS_DYNAMIC)

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

    # Log the originally configured submission time for today for clarity, even if actual is tomorrow
    logging.info(f"Original configured target submission time for today's rules: {SUBMIT_HOUR:02d}:{SUBMIT_MINUTE:02d}:{SUBMIT_SECOND:02d}")

    # --- Preparation Phase --- 
    logging.info("--- Starting Preparation Phase ---")
    
    preparation_halted = False
    for days_ahead in days_ahead_to_book:        
        # Reset account pointer and reshuffle accounts so that each user can be used once *per booking date*
        account_index = 0
        random.shuffle(accounts)  # fresh random ordering for this date
        booking_date_obj = datetime.now().date() + timedelta(days=days_ahead)
        logging.info(f"== Preparing bookings for {booking_date_obj.strftime('%A, %m/%d/%Y')} ({days_ahead} days ahead) ==")

        # Use a while loop to aggressively retry priorities instead of skipping them on failure
        priority_index = 0
        while priority_index < len(COURT_PRIORITIES):
            # Check for deadline before every single attempt
            if datetime.now() >= preparation_hard_stop_time:
                logging.warning(f"Approaching submission deadline ({PREPARATION_CUTOFF_SECONDS_DYNAMIC}s buffer). Halting further preparations.")
                preparation_halted = True
                break # Break from the while loop over priorities
            
            # Check for available accounts before every attempt
            if account_index >= len(accounts):
                logging.warning(f"No more accounts available. Stopping preparation for {booking_date_obj.strftime('%m/%d/%Y')}.")
                break # Stop processing priorities for this date if out of accounts

            priority = COURT_PRIORITIES[priority_index]
            prep_attempt_start_time = datetime.now() # Start timer for this instance
            # Ensure the variable exists even if setup_driver or login fails before assignment
            preparation_success = False
            # Get the next account
            username = accounts[account_index]
            user_data = USERS[username]
            court_number = priority["court"]
            preferred_time = priority["time"]
            logging.info(f"Priority #{priority_index+1}: Assigning {username} to prepare Court {court_number} at {preferred_time} for {booking_date_obj.strftime('%m/%d/%Y')}")

            booker = TennisBooker()
            try:
                if booker.driver and booker.login(user_data['email'], user_data['password']):
                    logging.debug(f"Attempting to prepare instance for {username} - {court_number} at {preferred_time} on {booking_date_obj.strftime('%m/%d/%Y')}")
                    preparation_success = booker.prepare_booking(
                        court_number,
                        booking_date_obj, 
                        preferred_time
                    )

                    if preparation_success:
                        prepared_instances.append(booker) # Keep instance open
                        account_index += 1 # Consume this account
                        priority_index += 1 # SUCCESS: Move to the next priority

                        # If this is the first successful prep, start the heartbeat thread
                        if pinger_thread is None:
                            logging.info("First instance prepared. Starting background keep-alive heartbeat thread.")
                            pinger_thread = threading.Thread(
                                target=keep_alive_pinger,
                                args=(prepared_instances, stop_pinger_event),
                                daemon=True  # Allow main program to exit without waiting
                            )
                            pinger_thread.start()
                            
                    else:
                        # FAILURE: Don't advance priority_index, just consume the account and retry this priority.
                        logging.warning(f"Closing browser for {username} due to FAILED PREPARATION for {booker.court_info_for_logging} (prepare_booking returned False). Retrying same priority with next account.")
                        booker.close()
                        account_index += 1 # Consume this account and try again
                else:
                    # Handle setup_driver failure or login failure
                    logging.warning(f"Skipping preparation for {username} due to setup/login failure. Closing browser and using next account for same priority.")
                    booker.close()
                    account_index += 1 # Consume this account

            except Exception as e:
                # Catch unexpected errors during the whole prep attempt for one user
                logging.error(f"UNEXPECTED EXCEPTION during preparation attempt for {username} - {booker.court_info_for_logging if booker else 'N/A'}: {str(e)}. Closing browser.")
                try:
                    booker.close()
                except Exception as close_err:
                    logging.error(f"Error closing browser after unexpected error for {username}: {close_err}")
                account_index += 1 # Consume account so we don't retry with a failed user
            
            # Check duration for this specific attempt
            prep_attempt_duration_seconds = (datetime.now() - prep_attempt_start_time).total_seconds()
            logging.debug(f"Preparation attempt for {username} - {court_number} at {preferred_time} took {prep_attempt_duration_seconds:.1f}s.")
            # Abort and retry if any single preparation attempt (success or failure) exceeds the time budget.
            if prep_attempt_duration_seconds > MAX_PREP_TIME_PER_INSTANCE_SECONDS and not preparation_success:
                logging.warning(
                    f"PREPARATION TIMEOUT: {username}'s attempt for Court {court_number} at {preferred_time} took "
                    f"{prep_attempt_duration_seconds:.1f}s (limit {MAX_PREP_TIME_PER_INSTANCE_SECONDS}s). "
                    f"Discarding this instance and retrying the same priority with next account."
                )

                # If the page did eventually prepare but took too long, close and remove the instance so it doesn't submit late.
                try:
                    booker.close()
                except Exception as close_err:
                    logging.error(f"Error closing slow browser instance for {username}: {close_err}")

                # If the (slow) instance had been added to the prepared list, remove it.
                if booker in prepared_instances:
                    prepared_instances.remove(booker)

                # Consume the account and retry the same priority with the next user.
                account_index += 1
                # Ensure we *do not* advance priority_index so that we retry this court/time.
                continue

        logging.info(f"== Finished preparation attempts for {booking_date_obj.strftime('%m/%d/%Y')} ==")

        if preparation_halted:
            logging.info("Preparation was halted due to approaching deadline. Moving to waiting/submission phase.")
            break # Break from days_ahead loop

    # --- End Preparation Phase ---
    # Stop the keep-alive pinger thread as we are moving to the final wait/submission
    if pinger_thread:
        logging.info("Preparation phase complete. Stopping heartbeat thread.")
        stop_pinger_event.set()
        pinger_thread.join(timeout=5) # Wait for the thread to finish, with a timeout

    if not prepared_instances:
        logging.info("No bookings were successfully prepared. Exiting.")
        return

    logging.info(f"--- Preparation Complete: {len(prepared_instances)} instances ready for submission ---")

    # --- Waiting Phase --- 
    # Replace simple sleep with an active wait loop that pings browsers
    wait_seconds = (target_submit_time - datetime.now()).total_seconds()
    if wait_seconds > 0:
        logging.info(f"Entering final waiting phase. Target: {target_submit_time.strftime('%Y-%m-%d %H:%M:%S')} ({wait_seconds:.2f}s from now).")
        # The heartbeat thread handled keep-alives during prep.
        # This final sleep is passive since it should be short.
        time.sleep(wait_seconds)
    else:
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
            time.sleep(random.uniform(0, SUBMIT_DELAY_MAX_SECONDS)) 
            booker_instance.submit_prepared_booking() # Click submit
            submit_attempts += 1

            # Staggering logic: Pause for 1 second after every 3rd submission, 
            # but not after the very last one.
            #if (idx + 1) % 3 == 0 and (idx + 1) < len(prepared_instances):
            #    logging.info(f"Pausing for 1 second after submitting batch ending with instance {idx+1}...")
            #    time.sleep(1) 
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
    # Perform a pre-flight check for internet before doing anything else
    if not check_internet_connection():
        # If it fails, log it and exit. The scheduler will try again tomorrow.
        logging.critical("Exiting script due to lack of internet connectivity.")
        exit()

    main() 