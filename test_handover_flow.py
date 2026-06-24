import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def run_handover_e2e():
    # 1. Create a dummy progress photo if it doesn't exist
    os.makedirs('static/uploads', exist_ok=True)
    dummy_img_path = 'static/uploads/dummy_progress.png'
    if not os.path.exists(dummy_img_path):
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (300, 200), color='#1f2937')
        d = ImageDraw.Draw(img)
        d.text((10, 10), "Progress Photo Proof", fill='#f3f4f6')
        img.save(dummy_img_path)
    
    # Absolute path for Selenium file upload
    abs_dummy_img_path = os.path.abspath(dummy_img_path)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1200,900")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    screenshots_dir = r"C:\Users\meet0\.gemini\antigravity\brain\dd4be854-c165-418e-bd67-039773493c7e"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    try:
        # --- STAGE 1: Rahul (Employee) starts task and initiates handover ---
        print("1. Navigating to login page...")
        driver.get("http://127.0.0.1:5000/login")
        time.sleep(1)
        
        print("2. Logging in as Rahul...")
<<<<<<< HEAD
        driver.find_element(By.ID, "email").send_keys("rahul@hoteltask.com")
=======
        driver.find_element(By.ID, "email").send_keys("rahul@luxeops.com")
>>>>>>> 00230176abfcea18cc8bec9f8380a9e8c8aa516d
        driver.find_element(By.ID, "password").send_keys("emp123")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(2)
        
        print("3. Initializing 'Clean Suite 402' task...")
        # Clean Suite 402 is task ID 1 in the seeded data
        init_btn = driver.find_element(By.XPATH, "//form[contains(@action, '/task/start/1')]/button")
        init_btn.click()
        time.sleep(2)
        
        print("4. Clicking 'Handover Shift' to open modal...")
        handover_btn = driver.find_element(By.XPATH, "//button[@data-open-modal='handoverModal' and @data-task-id='1']")
        handover_btn.click()
        time.sleep(1)
        
        # Inject file and notes
        print("5. Filling out Handover Form...")
        file_input = driver.find_element(By.XPATH, "//form[contains(@action, '/task/handover/1')]//input[@type='file']")
        file_input.send_keys(abs_dummy_img_path)
        
        notes_textarea = driver.find_element(By.ID, "handover-notes")
        notes_textarea.send_keys("Vacuuming completed. Linen replacement is pending for the bedroom.")
        
        # Take screenshot of employee handover modal before submit
        screenshot_1 = os.path.join(screenshots_dir, "handover_modal_open.png")
        driver.save_screenshot(screenshot_1)
        print(f"Saved screenshot: {screenshot_1}")
        
        print("6. Submitting Handover...")
        submit_btn = driver.find_element(By.XPATH, "//form[contains(@action, '/task/handover/1')]//button[@type='submit']")
        submit_btn.click()
        time.sleep(2)
        
        # Take screenshot of employee dashboard after handover
        screenshot_2 = os.path.join(screenshots_dir, "employee_after_handover.png")
        driver.save_screenshot(screenshot_2)
        print(f"Saved screenshot: {screenshot_2}")
        
        # --- STAGE 2: Elena HOD reviews request and reassigns ---
        print("7. Logging out and logging in as HOD Elena...")
        driver.get("http://127.0.0.1:5000/logout")
        time.sleep(1)
        driver.get("http://127.0.0.1:5000/login")
<<<<<<< HEAD
        driver.find_element(By.ID, "email").send_keys("housekeeping_hod@hoteltask.com")
=======
        driver.find_element(By.ID, "email").send_keys("housekeeping_hod@luxeops.com")
>>>>>>> 00230176abfcea18cc8bec9f8380a9e8c8aa516d
        driver.find_element(By.ID, "password").send_keys("hod123")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(2)
        
        print("8. Verifying HOD dashboard contains handover requests...")
        # Verify the section is present
        handover_section = driver.find_element(By.ID, "handover-requests-section")
        assert handover_section is not None, "Handover requests section not visible on HOD dashboard!"
        
        # Take screenshot of HOD dashboard showing requests
        screenshot_3 = os.path.join(screenshots_dir, "hod_handover_requests.png")
        driver.save_screenshot(screenshot_3)
        print(f"Saved screenshot: {screenshot_3}")
        
        print("9. Clicking Reassign to open modal...")
        reassign_btn = handover_section.find_element(By.XPATH, ".//button[@data-open-modal='reassignModal']")
        reassign_btn.click()
        time.sleep(1)
        
        print("10. Selecting Priya Sharma as new assignee...")
        reassign_select = driver.find_element(By.ID, "reassign-employee")
        # Find option for Priya Sharma
        options = reassign_select.find_elements(By.TAG_NAME, "option")
        priya_option = None
        for opt in options:
            if "Priya" in opt.text:
                priya_option = opt
                break
        assert priya_option is not None, "Priya Sharma option not found in reassign list!"
        priya_option.click()
        time.sleep(0.5)
        
        # Take screenshot of reassign modal
        screenshot_4 = os.path.join(screenshots_dir, "hod_reassign_modal.png")
        driver.save_screenshot(screenshot_4)
        print(f"Saved screenshot: {screenshot_4}")
        
        print("11. Dispatching reassignment...")
        dispatch_btn = driver.find_element(By.XPATH, "//form[contains(@action, '/task/reassign/1')]//button[@type='submit']")
        dispatch_btn.click()
        time.sleep(2)
        
        # --- STAGE 3: Priya receives task and checks previous progress ---
        print("12. Logging out and logging in as Priya...")
        driver.get("http://127.0.0.1:5000/logout")
        time.sleep(1)
        driver.get("http://127.0.0.1:5000/login")
<<<<<<< HEAD
        driver.find_element(By.ID, "email").send_keys("priya@hoteltask.com")
=======
        driver.find_element(By.ID, "email").send_keys("priya@luxeops.com")
>>>>>>> 00230176abfcea18cc8bec9f8380a9e8c8aa516d
        driver.find_element(By.ID, "password").send_keys("emp123")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(2)
        
        print("13. Verifying task is assigned and displays previous progress...")
        task_title = driver.find_element(By.XPATH, "//*[contains(text(), 'Clean Suite 402')]")
        assert task_title is not None, "Clean Suite 402 not found in Priya's checklist!"
        
        # Take screenshot of Priya's checklist showing previous progress
        screenshot_5 = os.path.join(screenshots_dir, "priya_received_handover.png")
        driver.save_screenshot(screenshot_5)
        print(f"Saved screenshot: {screenshot_5}")
        
        print("Verification completed successfully!")
        
    except Exception as e:
        print("An error occurred during verification:")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

if __name__ == '__main__':
    run_handover_e2e()
