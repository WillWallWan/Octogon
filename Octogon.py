import time
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta


def log_in(user):
    service = Service(executable_path=r'C:\Users\willy\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe')
    driver = webdriver.Chrome(service=service)

    
    # Initialize a wait object with a timeout of 10 seconds
    # wait = WebDriverWait(driver, 10)


    driver.get('https://rioc.civicpermits.com/')

    time.sleep(5)

    if user == "jen":
        login = 'jenni-wan@hotmail.com'
    elif user =="will":
        login = 'willy-wan@hotmail.com'

    driver.find_element(By.ID, 'loginEmail').send_keys(login)
    driver.find_element(By.ID, 'loginPassword').send_keys('Iluvrobin123321')

    # Click the Sign In button
    driver.find_element(By.XPATH, '//form[@id="login"]/div/table/tbody/tr/td/button').click()

    print("logged into account", user)
    
    return driver
    

def fill_out_form(driver, court_number):
    
    
    wait = WebDriverWait(driver, 10)

    
    # Add a wait to ensure login is successful and the next page loads.
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//a[@href="/Permits/New" and @class="button"]'))).click()
    
    # Venue Information
    wait.until(EC.element_to_be_clickable((By.ID, "activity"))).send_keys("Tennis Match")


    if court_number in (1, 4, 5, 6):
        court_name = f"Octagon Tennis Court {court_number}"  # dynamic court name
    if court_number in (2, 3):
        court_name = f"Octagon Tennis court {court_number}"

    site_dropdown = Select(wait.until(EC.element_to_be_clickable((By.ID, "site"))))
    site_dropdown.select_by_visible_text(court_name)

    time.sleep(0.2)

    add_facility_button = wait.until(EC.element_to_be_clickable((By.ID, "addFacilitySet")))
    driver.execute_script("arguments[0].click();", add_facility_button)

    if court_number == 1:
        checkbox_id = "036dfea4-c487-47b0-b7fe-c9cbe52b7c98"
    elif court_number == 2:
        checkbox_id = "175bdff8-016e-46ab-a9df-829fe40c0754"
    elif court_number == 3:
        checkbox_id = "9bdef00b-afa0-4b6b-bf9a-75899f7f97c7"
    elif court_number == 4:
        checkbox_id = "d311851d-ce53-49fc-9662-42adcda26109"
    elif court_number == 5:
        checkbox_id = "8a5ca8e8-3be0-4145-a4ef-91a69671295b"
    elif court_number == 6:
        checkbox_id = "77c7f42c-8891-4818-a610-d5c1027c62fe"
    else:
        # handle other cases or raise an exception
        raise ValueError(f"Unknown court number: {court_number}")
           
    
    facility_checkbox = wait.until(EC.element_to_be_clickable((By.ID, checkbox_id)))
    if not facility_checkbox.is_selected():
        facility_checkbox.click()
    
    # Get the date for the day after tomorrow
    day_after_tomorrow = datetime.today().date() + timedelta(days=2)

    # Format the date in the desired format
    formatted_date = day_after_tomorrow.strftime('%m/%d/%Y')
    

    wait.until(EC.element_to_be_clickable((By.ID, "event0"))).send_keys(formatted_date)

    body_element = driver.find_element(By.TAG_NAME, 'body')
    body_element.click()

    start_hour_dropdown = Select(wait.until(EC.element_to_be_clickable((By.NAME, "startHour"))))
    start_hour_dropdown.select_by_value("18")

    end_hour_dropdown = Select(wait.until(EC.element_to_be_clickable((By.NAME, "endHour"))))
    end_hour_dropdown.select_by_value("19")

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".controlArea button"))).click()
    
    time.sleep(0.2)

    # Permit Questions
    wait.until(EC.element_to_be_clickable((By.ID, "11e79e5d3daf4712b9e6418d2691b976"))).send_keys("Playing tennis")
    wait.until(EC.element_to_be_clickable((By.ID, "af8966101be44676b4ee564b052e1e87"))).send_keys("2")
    wait.until(EC.element_to_be_clickable((By.ID, "f28f0dbea8b5438495778b0bb0ddcd93"))).send_keys("No")
    wait.until(EC.element_to_be_clickable((By.ID, "d46cb434558845fb9e0318ab6832e427"))).send_keys("No")
    wait.until(EC.element_to_be_clickable((By.ID, "7ee8568916454adaa207e3888be54818"))).send_keys("No")
    wait.until(EC.element_to_be_clickable((By.ID, "0ce54956c4b14746ae5d364507da1e85"))).send_keys("None")
    wait.until(EC.element_to_be_clickable((By.ID, "6b1dda4172f840c7879662bcab1819db"))).send_keys("None")
    wait.until(EC.element_to_be_clickable((By.ID, "a31f4297075e4dab8c0ef154f2b9b1c1"))).send_keys("None")

    previous_permit_dropdown = Select(wait.until(EC.element_to_be_clickable((By.ID, "3754dcef7216446b9cc4bf1cd0f12a2e"))))
    previous_permit_dropdown.select_by_visible_text("No")

    security_dropdown = Select(wait.until(EC.element_to_be_clickable((By.ID, "06b3f73192a84fd6b88758e56a64c3ad"))))
    security_dropdown.select_by_visible_text("No")

    wait.until(EC.element_to_be_clickable((By.ID, "acceptTerms"))).click()

    time.sleep(0.2)


    try:
        submit_button = driver.find_element(By.XPATH, "//button[@id='cancelNewPermitRequest']/preceding-sibling::button")
        
        
        driver.execute_script("arguments[0].scrollIntoView();", submit_button)

        time.sleep(0.2)

        # Click the button
        driver.execute_script("arguments[0].click();", submit_button)

        print("submitted request for court", court_number)

    except Exception as e:
        print("Error finding the submit button:", str(e))

    

driver = log_in("jen")
fill_out_form(driver, 5)


driver = log_in("will")
fill_out_form(driver, 6)
#fill_out_form(driver, 3)
#fill_out_form(driver, 4)
#fill_out_form(driver, 5)
#fill_out_form(driver, 6)

time.sleep(5)

driver.close()