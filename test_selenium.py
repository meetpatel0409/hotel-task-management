import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def test_manager_dashboard_filtering():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print("Navigating to login page...")
        driver.get("http://127.0.0.1:5000/login")
        time.sleep(1)
        
        print("Logging in as Manager...")
        email_input = driver.find_element(By.ID, "email")
<<<<<<< HEAD
        email_input.send_keys("manager@hoteltask.com")
=======
        email_input.send_keys("manager@luxeops.com")
>>>>>>> 00230176abfcea18cc8bec9f8380a9e8c8aa516d
        
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys("manager123")
        
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        time.sleep(2)
        
        print("Current URL:", driver.current_url)
        
        # Verify clock is removed
        clock_elements = driver.find_elements(By.ID, "clock-display")
        assert len(clock_elements) == 0, "Clock display should be removed!"
        print("Verified: Clock display is completely removed from top right corner.")
        
        # Check active work count card
        active_card = driver.find_element(By.XPATH, "//div[@data-filter='active']")
        active_value = active_card.find_element(By.CLASS_NAME, "stat-value").text
        print(f"Active Work card value: {active_value} (Expected: 3)")
        assert active_value == "3", f"Expected active work count 3, got {active_value}"
        
        # Print table status
        print("\nInitial rows status:")
        rows = driver.find_elements(By.CLASS_NAME, "task-row")
        for i, row in enumerate(rows):
            print(f"Row {i}: title='{row.find_element(By.TAG_NAME, 'strong').text}', dept='{row.get_attribute('data-department')}', status='{row.get_attribute('data-status')}', display='{row.value_of_css_property('display')}'")
            
        # Click "Active Work" card
        print("\nClicking 'Active Work' card...")
        active_card.click()
        time.sleep(1)
        
        print("Rows status after clicking 'Active Work':")
        for i, row in enumerate(rows):
            print(f"Row {i}: title='{row.find_element(By.TAG_NAME, 'strong').text}', display='{row.value_of_css_property('display')}'")
            
        # Select "Housekeeping" department filter
        print("\nSelecting 'Housekeeping' department filter...")
        dept_select = driver.find_element(By.ID, "table-dept-filter")
        dept_select.send_keys("Housekeeping")
        time.sleep(1)
        
        print("Rows status after filtering by 'Housekeeping' department:")
        for i, row in enumerate(rows):
            print(f"Row {i}: title='{row.find_element(By.TAG_NAME, 'strong').text}', display='{row.value_of_css_property('display')}'")
            
        # Select "All Departments" department filter
        print("\nSelecting 'All Departments' filter...")
        dept_select.send_keys("All Departments")
        time.sleep(1)
        
        print("Rows status after resetting department filter:")
        for i, row in enumerate(rows):
            print(f"Row {i}: title='{row.find_element(By.TAG_NAME, 'strong').text}', display='{row.value_of_css_property('display')}'")
            
    finally:
        driver.quit()

if __name__ == '__main__':
    test_manager_dashboard_filtering()
