"""Pinterest automation using Selenium (No API required)"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont

# Pinterest credentials
PINTEREST_EMAIL = os.environ.get("PINTEREST_EMAIL")
PINTEREST_PASSWORD = os.environ.get("PINTEREST_PASSWORD")
BLOG_SITE = "https://ur-cristiano-fc.github.io"

# Pin settings
PIN_WIDTH = 1000
PIN_HEIGHT = 1500

def create_pinterest_driver():
    """Create Selenium Chrome driver with proper configuration for GitHub Actions"""
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    # Critical headless flags
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Anti-detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Driver created using webdriver-manager")
    except Exception as e:
        print(f"⚠️ Webdriver-manager failed: {e}. Attempting fallback...")
        driver = webdriver.Chrome(options=chrome_options)
    
    return driver

def login_to_pinterest(driver):
    """Login to Pinterest"""
    try:
        print("🔐 Logging into Pinterest...")
        driver.get("https://www.pinterest.com/login/")
        time.sleep(5)
        
        # Enter email
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_input.clear()
        email_input.send_keys(PINTEREST_EMAIL)
        time.sleep(2)
        
        # Enter password
        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys(PINTEREST_PASSWORD)
        time.sleep(2)
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        print("🔘 Login button clicked")
        
        # Wait for dashboard
        time.sleep(15)
        
        if "login" in driver.current_url:
            print("❌ Login failed - still on login page")
            driver.save_screenshot("pinterest_login_failed.png")
            return False
            
        print("✅ Logged in successfully")
        return True
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        driver.save_screenshot("pinterest_login_error.png")
        return False

def create_pin_image(base_image_path, hook_text, output_path):
    """Create simple pin image"""
    print(f"🎨 Creating pin image from: {base_image_path}")
    
    try:
        base_img = Image.open(base_image_path).convert('RGB')
        pin = Image.new('RGB', (PIN_WIDTH, PIN_HEIGHT), (255, 255, 255))
        
        # Resize base image (top 60%)
        img_height = int(PIN_HEIGHT * 0.6)
        aspect_ratio = base_img.height / base_img.width
        new_width = PIN_WIDTH
        new_height = int(new_width * aspect_ratio)
        
        if new_height > img_height:
            new_height = img_height
            new_width = int(new_height / aspect_ratio)
        
        base_img = base_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        x_offset = (PIN_WIDTH - new_width) // 2
        pin.paste(base_img, (x_offset, 0))
        
        # Text area (Dark Grey)
        draw = ImageDraw.Draw(pin)
        draw.rectangle([(0, img_height), (PIN_WIDTH, PIN_HEIGHT)], fill=(45, 52, 54))
        
        # Red Accent Line
        draw.rectangle([(0, img_height), (PIN_WIDTH, img_height + 15)], fill=(255, 71, 87))
        
        # Font (Fallback to default if custom not found)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()

        # Draw Hook Text
        text_y = img_height + 100
        words = hook_text.split()
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > PIN_WIDTH - 100:
                current_line.pop()
                line_to_draw = ' '.join(current_line)
                bbox = draw.textbbox((0, 0), line_to_draw, font=font)
                x = (PIN_WIDTH - (bbox[2] - bbox[0])) // 2
                draw.text((x, text_y), line_to_draw, font=font, fill=(255, 255, 255))
                text_y += 80
                current_line = [word]
        
        if current_line:
            line_to_draw = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), line_to_draw, font=font)
            x = (PIN_WIDTH - (bbox[2] - bbox[0])) // 2
            draw.text((x, text_y), line_to_draw, font=font, fill=(255, 255, 255))

        pin.save(output_path, 'PNG')
        return output_path
    except Exception as e:
        print(f"⚠️ Image creation failed: {e}")
        return None

def upload_pin_to_pinterest(driver, image_path, title, description, link):
    """Upload pin using Selenium"""
    try:
        print(f"📤 Uploading pin to Pinterest...")
        driver.get("https://www.pinterest.com/pin-builder/")
        time.sleep(8)
        
        # 1. Upload Image
        try:
            file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(os.path.abspath(image_path))
            print("📸 Image uploaded")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Image upload failed: {e}")
            driver.save_screenshot("pinterest_upload_fail.png")
            return False

        # 2. Enter Title (Using more robust JS injection if click fails)
        try:
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='pin-draft-title']"))
            )
            driver.execute_script("arguments[0].click();", title_input)
            time.sleep(1)
            title_input.send_keys(title[:100])
            print(f"✏️ Title entered")
        except Exception as e:
            print(f"❌ Title entry failed: {e}")
            return False

        # 3. Enter Description
        try:
            desc_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-description']")
            driver.execute_script("arguments[0].click();", desc_input)
            desc_input.send_keys(description[:500])
            print(f"✏️ Description entered")
        except:
            print("⚠️ Description skipped")

        # 4. Enter Link
        try:
            link_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-link']")
            driver.execute_script("arguments[0].click();", link_input)
            link_input.send_keys(link)
            print(f"🔗 Link added")
        except:
            print("⚠️ Link skipped")

        # ==========================================
        # 5. SELECT BOARD (The Missing Step!)
        # ==========================================
        try:
            print("📋 Selecting board...")
            # Click the board dropdown
            board_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test-id='board-dropdown-select-button']"))
            )
            board_dropdown.click()
            time.sleep(2)
            
            # Select the first available board in the list
            first_board = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test-id='board-row-item']"))
            )
            board_name = first_board.text
            first_board.click()
            print(f"✅ Board selected: {board_name}")
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Failed to select board: {e}")
            driver.save_screenshot("pinterest_board_fail.png")
            return False

        # 6. Click Save/Publish
        try:
            save_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test-id='board-dropdown-save-button']"))
            )
            save_button.click()
            print("📌 Save button clicked")
            
            # Wait for confirmation
            time.sleep(10)
            driver.save_screenshot("pinterest_success.png")
            return True
            
        except Exception as e:
            print(f"❌ Publish failed: {e}")
            driver.save_screenshot("pinterest_publish_fail.png")
            return False
            
    except Exception as e:
        print(f"❌ General upload error: {e}")
        return False

def post_to_pinterest_selenium(title, focus_kw, permalink, featured_image_path, description, hook_text):
    """Main execution function"""
    if not PINTEREST_EMAIL or not PINTEREST_PASSWORD:
        print("❌ Pinterest credentials missing")
        return False
    
    driver = None
    pin_path = f"temp_pin_{permalink}.png"
    
    try:
        # Create Pin
        if not create_pin_image(featured_image_path, hook_text, pin_path):
            return False

        # Initialize Driver
        driver = create_pinterest_driver()
        
        # Login
        if not login_to_pinterest(driver):
            return False
            
        # Post
        article_url = f"{BLOG_SITE}/{permalink}"
        hashtags = f"#{focus_kw.replace(' ', '')} #CristianoRonaldo #CR7"
        full_desc = f"{description}\n\n{hashtags}"
        
        success = upload_pin_to_pinterest(driver, pin_path, title, full_desc, article_url)
        
        if success:
            print(f"✅ Pinterest posting successful!")
        else:
            print(f"❌ Pinterest posting failed during upload.")
            
        return success
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()
        if os.path.exists(pin_path):
            os.remove(pin_path)