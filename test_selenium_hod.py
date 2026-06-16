import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def test_hod_dashboard():
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
        
        print("Logging in as HOD...")
        email_input = driver.find_element(By.ID, "email")
        email_input.send_keys("housekeeping_hod@luxeops.com")
        
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys("hod123")
        
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        time.sleep(2)
        
        print("Current URL:", driver.current_url)
        
        print("\n--- Console Logs on HOD Page ---")
        for entry in driver.get_log('browser'):
            print(entry)
        print("--------------------------------\n")
        
        # Print table status
        print("Initial rows status:")
        rows = driver.find_elements(By.CLASS_NAME, "task-row")
        for i, row in enumerate(rows):
            print(f"Row {i}: title='{row.find_element(By.TAG_NAME, 'strong').text}', status='{row.get_attribute('data-status')}', display='{row.value_of_css_property('display')}'")
            
        # Click "Pending Staff" card
        print("\nClicking 'Pending Staff' card...")
        pending_card = driver.find_element(By.XPATH, "//div[@data-filter='Pending']")
        pending_card.click()
        time.sleep(1)
        
        print("Rows status after clicking 'Pending Staff':")
        for i, row in enumerate(rows):
            print(f"Row {i}: title='{row.find_element(By.TAG_NAME, 'strong').text}', display='{row.value_of_css_property('display')}'")
            
        # Click "Completed" card
        print("\nClicking 'Completed' card...")
        completed_card = driver.find_element(By.XPATH, "//div[@data-filter='completed']")
        completed_card.click()
        time.sleep(1)
        
        print("Rows status after clicking 'Completed':")
        for i, row in enumerate(rows):
            print(f"Row {i}: title='{row.find_element(By.TAG_NAME, 'strong').text}', display='{row.value_of_css_property('display')}'")
            
    finally:
        driver.quit()

if __name__ == '__main__':
    test_hod_dashboard()
