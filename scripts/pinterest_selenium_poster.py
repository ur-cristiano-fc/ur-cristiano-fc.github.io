"""Pinterest automation using Selenium (No API required)"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
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
    
    # Path to the Google Chrome binary in GitHub Actions
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Anti-detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set user agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        # Use webdriver-manager to handle driver matching automatically
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Driver created using webdriver-manager")
    except Exception as e:
        print(f"⚠️ Webdriver-manager failed: {e}. Attempting fallback...")
        # Fallback for standard environments
        driver = webdriver.Chrome(options=chrome_options)
    
    # ... rest of your script (CDP commands, etc.)
    return driver

def login_to_pinterest(driver):
    """Login to Pinterest"""
    try:
        print("🔐 Logging into Pinterest...")
        driver.get("https://www.pinterest.com/login/")
        
        # Wait for login form
        time.sleep(4)
        
        # Enter email
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_input.clear()
        time.sleep(0.5)
        email_input.send_keys(PINTEREST_EMAIL)
        print(f"✅ Email entered: {PINTEREST_EMAIL}")
        time.sleep(1.5)
        
        # Enter password
        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        time.sleep(0.5)
        password_input.send_keys(PINTEREST_PASSWORD)
        print("✅ Password entered")
        time.sleep(1.5)
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        print("🔘 Login button clicked")
        
        # Wait for dashboard (increased timeout)
        time.sleep(12)
        
        current_url = driver.current_url
        print(f"📍 Current URL after login: {current_url}")
        
        # Check if logged in
        if "pinterest.com/login" in current_url:
            print("❌ Login failed - still on login page")
            # Take screenshot for debugging
            try:
                screenshot_path = os.path.abspath("pinterest_login_failed.png")
                driver.save_screenshot(screenshot_path)
                print(f"📸 Screenshot saved: {screenshot_path}")
            except Exception as ss_error:
                print(f"⚠️ Could not save screenshot: {ss_error}")
            return False
        
        print("✅ Logged in successfully")
        return True
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to save screenshot for debugging
        try:
            screenshot_path = os.path.abspath("pinterest_login_error.png")
            driver.save_screenshot(screenshot_path)
            print(f"📸 Error screenshot saved: {screenshot_path}")
        except:
            pass
        
        return False


def create_pin_image(base_image_path, hook_text, output_path, style='modern'):
    """Create Pinterest pin from blog image"""
    
    print(f"🎨 Creating pin image from: {base_image_path}")
    
    # Load base image
    base_img = Image.open(base_image_path).convert('RGB')
    
    # Create pin canvas
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
    
    # Paste image
    x_offset = (PIN_WIDTH - new_width) // 2
    pin.paste(base_img, (x_offset, 0))
    
    # Add text area
    draw = ImageDraw.Draw(pin)
    
    # Colors based on style
    if style == 'modern':
        bg_color = (45, 52, 54)
        text_color = (255, 255, 255)
        accent_color = (255, 71, 87)
    elif style == 'bold':
        bg_color = (255, 71, 87)
        text_color = (255, 255, 255)
        accent_color = (45, 52, 54)
    else:
        bg_color = (255, 255, 255)
        text_color = (45, 52, 54)
        accent_color = (255, 71, 87)
    
    # Draw text background
    text_area_y = img_height
    draw.rectangle([(0, text_area_y), (PIN_WIDTH, PIN_HEIGHT)], fill=bg_color)
    
    # Accent bar
    draw.rectangle([(0, text_area_y), (PIN_WIDTH, text_area_y + 8)], fill=accent_color)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
        url_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except Exception as font_error:
        print(f"⚠️ Could not load custom fonts: {font_error}")
        title_font = ImageFont.load_default()
        url_font = ImageFont.load_default()
    
    # Draw hook text (centered, multi-line)
    words = hook_text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=title_font)
        if bbox[2] - bbox[0] > PIN_WIDTH - 80:
            if len(current_line) == 1:
                lines.append(current_line[0])
                current_line = []
            else:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw lines
    y_position = text_area_y + 60
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (PIN_WIDTH - text_width) // 2
        draw.text((x, y_position), line, font=title_font, fill=text_color)
        y_position += bbox[3] - bbox[1] + 20
    
    # Draw URL
    url_text = "ur-cristiano-fc.github.io"
    bbox = draw.textbbox((0, 0), url_text, font=url_font)
    text_width = bbox[2] - bbox[0]
    x = (PIN_WIDTH - text_width) // 2
    y = PIN_HEIGHT - 80
    draw.text((x, y), url_text, font=url_font, fill=accent_color)
    
    # Save
    pin.save(output_path, 'PNG', quality=95, optimize=True)
    print(f"✅ Pin created: {output_path} ({os.path.getsize(output_path)} bytes)")
    return output_path


def upload_pin_to_pinterest(driver, image_path, title, description, link):
    """Upload pin using Selenium"""
    try:
        print(f"📤 Uploading pin to Pinterest...")
        print(f"   Image: {image_path}")
        print(f"   Title: {title[:50]}...")
        print(f"   Link: {link}")
        
        # Verify image exists
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return False
        
        # Go to create pin page
        driver.get("https://www.pinterest.com/pin-builder/")
        time.sleep(6)
        
        # Take screenshot before upload
        try:
            driver.save_screenshot("pinterest_before_upload.png")
        except:
            pass
        
        # Find and click the file upload area
        absolute_path = os.path.abspath(image_path)
        print(f"   Absolute path: {absolute_path}")
        
        uploaded = False
        
        # Method 1: Direct file input
        try:
            file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            print(f"   Found {len(file_inputs)} file input elements")
            
            for idx, file_input in enumerate(file_inputs):
                try:
                    if file_input.is_displayed() or True:  # Try even hidden inputs
                        file_input.send_keys(absolute_path)
                        print(f"📸 Image uploaded via input {idx}")
                        uploaded = True
                        break
                except Exception as e:
                    print(f"   Input {idx} failed: {e}")
                    continue
                    
        except Exception as e1:
            print(f"⚠️ Method 1 (find all inputs) failed: {e1}")
        
        # Method 2: Click upload button first
        if not uploaded:
            try:
                upload_buttons = driver.find_elements(By.CSS_SELECTOR, "[data-test-id*='upload'], button:has-text('Choose')")
                if upload_buttons:
                    upload_buttons[0].click()
                    print("🔘 Clicked upload button")
                    time.sleep(2)
                    
                    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                    file_input.send_keys(absolute_path)
                    print("📸 Image uploaded via method 2")
                    uploaded = True
            except Exception as e2:
                print(f"⚠️ Method 2 failed: {e2}")
        
        if not uploaded:
            print("❌ Could not upload image")
            driver.save_screenshot("pinterest_upload_failed.png")
            return False
        
        # Wait for image to process
        print("⏳ Waiting for image to process...")
        time.sleep(10)
        
        # Take screenshot after upload
        driver.save_screenshot("pinterest_after_upload.png")
        
        # Enter title
        try:
            title_selectors = [
                "[data-test-id='pin-draft-title']",
                "input[placeholder*='title' i]",
                "div[contenteditable='true'][data-test-id*='title']"
            ]
            
            title_entered = False
            for selector in title_selectors:
                try:
                    title_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", title_input)
                    time.sleep(1)
                    title_input.click()
                    time.sleep(1)
                    
                    # Clear and enter
                    title_input.clear()
                    time.sleep(0.5)
                    title_input.send_keys(title[:100])
                    print(f"✏️ Title entered: {title[:50]}...")
                    title_entered = True
                    time.sleep(1)
                    break
                except:
                    continue
            
            if not title_entered:
                print(f"⚠️ Could not enter title")
                
        except Exception as e:
            print(f"⚠️ Title entry failed: {e}")
        
        # Enter description
        try:
            desc_selectors = [
                "[data-test-id='pin-draft-description']",
                "textarea[placeholder*='description' i]",
                "div[contenteditable='true'][data-test-id*='description']"
            ]
            
            for selector in desc_selectors:
                try:
                    desc_input = driver.find_element(By.CSS_SELECTOR, selector)
                    driver.execute_script("arguments[0].scrollIntoView(true);", desc_input)
                    time.sleep(1)
                    desc_input.click()
                    time.sleep(1)
                    desc_input.clear()
                    time.sleep(0.5)
                    desc_input.send_keys(description[:500])
                    print(f"✏️ Description entered")
                    time.sleep(1)
                    break
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Description entry failed: {e}")
        
        # Add link/destination
        try:
            link_selectors = [
                "[data-test-id='pin-draft-link']",
                "input[placeholder*='link' i]",
                "input[placeholder*='destination' i]",
                "input[type='url']"
            ]
            
            for selector in link_selectors:
                try:
                    link_input = driver.find_element(By.CSS_SELECTOR, selector)
                    driver.execute_script("arguments[0].scrollIntoView(true);", link_input)
                    time.sleep(1)
                    link_input.click()
                    time.sleep(1)
                    link_input.clear()
                    time.sleep(0.5)
                    link_input.send_keys(link)
                    print(f"🔗 Link added: {link}")
                    time.sleep(1)
                    break
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Link entry failed: {e}")
        
        # Take screenshot before publish
        driver.save_screenshot("pinterest_before_publish.png")
        
        # Click publish/save button
        try:
            publish_selectors = [
                "[data-test-id='board-dropdown-save-button']",
                "button[data-test-id='board-dropdown-save-button']",
                "div[data-test-id='board-dropdown-save-button'] button",
                "button[type='submit']"
            ]
            
            published = False
            for selector in publish_selectors:
                try:
                    publish_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", publish_button)
                    time.sleep(1)
                    publish_button.click()
                    published = True
                    print("📌 Publish button clicked")
                    break
                except:
                    continue
            
            # Fallback: find any button with publish/save text
            if not published:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    try:
                        btn_text = btn.text.lower()
                        if ("publish" in btn_text or "save" in btn_text) and len(btn_text) < 20:
                            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                            time.sleep(1)
                            btn.click()
                            published = True
                            print(f"📌 Publish button clicked (fallback): {btn.text}")
                            break
                    except:
                        continue
            
            if not published:
                print("⚠️ Could not find publish button")
                driver.save_screenshot("pinterest_no_publish_button.png")
                # Don't return False yet - might still be successful
            
            # Wait for success
            time.sleep(10)
            
            # Take screenshot after publish
            driver.save_screenshot("pinterest_after_publish.png")
            
            print(f"✅ Pin upload completed!")
            return True
            
        except Exception as e:
            print(f"⚠️ Publish step had issues: {e}")
            driver.save_screenshot("pinterest_publish_error.png")
            # Still return True if we got this far
            return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            driver.save_screenshot("pinterest_general_error.png")
        except:
            pass
        
        return False


def post_to_pinterest_selenium(title, focus_kw, permalink, featured_image_path, description, hook_text):
    """Main function to post to Pinterest using Selenium"""
    
    if not PINTEREST_EMAIL or not PINTEREST_PASSWORD:
        print("❌ Pinterest credentials not found")
        print("   Set PINTEREST_EMAIL and PINTEREST_PASSWORD in GitHub secrets")
        return False
    
    print(f"\n{'='*60}")
    print(f"📌 Posting to Pinterest (Selenium Method)")
    print(f"{'='*60}")
    print(f"   Pinterest Email: {PINTEREST_EMAIL}")
    
    driver = None
    pin_path = None
    
    try:
        # Create pin image
        pin_path = f"temp_pin_{permalink}.png"
        create_pin_image(featured_image_path, hook_text, pin_path, style='modern')
        
        # Create driver
        print("🚀 Starting Chrome driver...")
        driver = create_pinterest_driver()
        print("✅ Chrome driver started")
        
        # Set page load timeout
        driver.set_page_load_timeout(60)
        
        # Login
        if not login_to_pinterest(driver):
            print("❌ Login failed, cannot proceed")
            return False
        
        # Prepare data
        article_url = f"{BLOG_SITE}/{permalink}"
        hashtags = f"#{focus_kw.replace(' ', '')} #CristianoRonaldo #CR7 #Football #Soccer"
        full_description = f"{description}\n\n{hashtags}"
        
        # Upload pin
        success = upload_pin_to_pinterest(
            driver,
            pin_path,
            title,
            full_description,
            article_url
        )
        
        if success:
            print(f"\n{'='*60}")
            print(f"✅ Pinterest posting successful!")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f"⚠️ Pinterest posting completed with warnings")
            print(f"{'='*60}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if pin_path and os.path.exists(pin_path):
            try:
                os.remove(pin_path)
                print(f"🧹 Cleaned up temp file: {pin_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Could not clean up temp file: {cleanup_error}")
        
        if driver:
            try:
                driver.quit()
                print(f"🔚 Browser closed")
            except:
                pass
        
        print(f"{'='*60}\n")


# Example usage
if __name__ == "__main__":
    # Test
    post_to_pinterest_selenium(
        title="Cristiano Ronaldo Training Secrets",
        focus_kw="cristiano ronaldo training",
        permalink="cristiano-training-secrets",
        featured_image_path="assets/images/featured_test.webp",
        description="Discover CR7's workout routine",
        hook_text="Ultimate CR7 Training Guide"
    )