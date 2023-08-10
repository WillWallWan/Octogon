from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def fill_out_form():
    service = Service(executable_path=r'C:\Users\willy\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe')
    driver = webdriver.Chrome(service=service)

    driver.get("https://rioc.civicpermits.com/Permits/New")

    # Initialize a wait object with a timeout of 10 seconds
    wait = WebDriverWait(driver, 10)

    # Venue Information
    wait.until(EC.element_to_be_clickable((By.ID, "activity"))).send_keys("Tennis Match")

    site_dropdown = Select(wait.until(EC.element_to_be_clickable((By.ID, "site"))))
    site_dropdown.select_by_visible_text("Octagon Tennis Court 6")

    add_facility_button = wait.until(EC.element_to_be_clickable((By.ID, "addFacilitySet")))
    driver.execute_script("arguments[0].click();", add_facility_button)

    facility_checkbox = wait.until(EC.element_to_be_clickable((By.ID, "77c7f42c-8891-4818-a610-d5c1027c62fe")))
    if not facility_checkbox.is_selected():
        facility_checkbox.click()

    wait.until(EC.element_to_be_clickable((By.ID, "event0"))).send_keys("YYYY-MM-DD")

    start_hour_dropdown = Select(wait.until(EC.element_to_be_clickable((By.NAME, "startHour"))))
    start_hour_dropdown.select_by_value("12")

    end_hour_dropdown = Select(wait.until(EC.element_to_be_clickable((By.NAME, "endHour"))))
    end_hour_dropdown.select_by_value("13")

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".controlArea button"))).click()

    # Permit Questions
    wait.until(EC.element_to_be_clickable((By.ID, "11e79e5d3daf4712b9e6418d2691b976"))).send_keys("Playing tennis.")
    wait.until(EC.element_to_be_clickable((By.ID, "af8966101be44676b4ee564b052e1e87"))).send_keys("10")
    wait.until(EC.element_to_be_clickable((By.ID, "f28f0dbea8b5438495778b0bb0ddcd93"))).send_keys("No charge.")
    wait.until(EC.element_to_be_clickable((By.ID, "d46cb434558845fb9e0318ab6832e427"))).send_keys("No charge.")
    wait.until(EC.element_to_be_clickable((By.ID, "7ee8568916454adaa207e3888be54818"))).send_keys("Yes, can also do next weekend.")
    wait.until(EC.element_to_be_clickable((By.ID, "0ce54956c4b14746ae5d364507da1e85"))).send_keys("No amplified sound.")
    wait.until(EC.element_to_be_clickable((By.ID, "6b1dda4172f840c7879662bcab1819db"))).send_keys("No advertisement.")
    wait.until(EC.element_to_be_clickable((By.ID, "a31f4297075e4dab8c0ef154f2b9b1c1"))).send_keys("2 cars and 1 van.")

    previous_permit_dropdown = Select(wait.until(EC.element_to_be_clickable((By.ID, "3754dcef7216446b9cc4bf1cd0f12a2e"))))
    previous_permit_dropdown.select_by_visible_text("No")

    security_dropdown = Select(wait.until(EC.element_to_be_clickable((By.ID, "06b3f73192a84fd6b88758e56a64c3ad"))))
    security_dropdown.select_by_visible_text("No")

    wait.until(EC.element_to_be_clickable((By.ID, "acceptTerms"))).click()

    # Commenting out the submit to prevent accidental submissions
    # driver.find_element(By.CSS_SELECTOR, ".controlArea button").click()

    driver.close()

fill_out_form()