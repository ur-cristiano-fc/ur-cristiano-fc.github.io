"""Pinterest automation using Selenium (No API required)"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
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
    """Create Selenium Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run without opening browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def login_to_pinterest(driver):
    """Login to Pinterest"""
    try:
        print("🔐 Logging into Pinterest...")
        driver.get("https://www.pinterest.com/login/")
        
        # Wait for login form
        time.sleep(3)
        
        # Enter email
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_input.clear()
        email_input.send_keys(PINTEREST_EMAIL)
        time.sleep(1)
        
        # Enter password
        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys(PINTEREST_PASSWORD)
        time.sleep(1)
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for dashboard (increased timeout)
        time.sleep(8)
        
        # Check if logged in
        if "pinterest.com/login" in driver.current_url:
            print("❌ Login failed - still on login page")
            return False
        
        print("✅ Logged in successfully")
        return True
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_pin_image(base_image_path, hook_text, output_path, style='modern'):
    """Create Pinterest pin from blog image"""
    
    # Load base image
    base_img = Image.open(base_image_path)
    
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
    except:
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
    print(f"✅ Pin created: {output_path}")
    return output_path


def upload_pin_to_pinterest(driver, image_path, title, description, link):
    """Upload pin using Selenium"""
    try:
        print(f"📤 Uploading pin to Pinterest...")
        
        # Go to create pin page
        driver.get("https://www.pinterest.com/pin-builder/")
        time.sleep(4)
        
        # Find and click the file upload area
        try:
            # Method 1: Direct file input
            file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='image']")
            file_input.send_keys(os.path.abspath(image_path))
            print("📸 Image uploaded")
            time.sleep(6)  # Wait for image to process
            
        except:
            # Method 2: Click upload button first
            upload_button = driver.find_element(By.CSS_SELECTOR, "[data-test-id='upload-btn']")
            upload_button.click()
            time.sleep(2)
            
            file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(os.path.abspath(image_path))
            print("📸 Image uploaded")
            time.sleep(6)
        
        # Enter title
        try:
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='pin-draft-title'], input[placeholder*='title' i]"))
            )
            title_input.click()
            time.sleep(1)
            title_input.clear()
            title_input.send_keys(title[:100])
            print(f"✍️ Title entered: {title[:50]}...")
            time.sleep(1)
            
        except Exception as e:
            print(f"⚠️ Could not enter title: {e}")
        
        # Enter description
        try:
            desc_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-description'], textarea[placeholder*='description' i]")
            desc_input.click()
            time.sleep(1)
            desc_input.clear()
            desc_input.send_keys(description[:500])
            print(f"✍️ Description entered")
            time.sleep(1)
            
        except Exception as e:
            print(f"⚠️ Could not enter description: {e}")
        
        # Add link/destination
        try:
            link_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-link'], input[placeholder*='link' i], input[placeholder*='destination' i]")
            link_input.click()
            time.sleep(1)
            link_input.clear()
            link_input.send_keys(link)
            print(f"🔗 Link added: {link}")
            time.sleep(1)
            
        except Exception as e:
            print(f"⚠️ Could not add link: {e}")
        
        # Click publish/save button
        try:
            # Try different selectors for publish button
            publish_selectors = [
                "[data-test-id='board-dropdown-save-button']",
                "button[type='button']:has-text('Publish')",
                "button:has-text('Save')",
                "div[data-test-id='pin-builder-save-button']"
            ]
            
            published = False
            for selector in publish_selectors:
                try:
                    publish_button = driver.find_element(By.CSS_SELECTOR, selector)
                    publish_button.click()
                    published = True
                    print("📌 Publish button clicked")
                    break
                except:
                    continue
            
            if not published:
                # Fallback: find any button with "Publish" or "Save" text
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if "publish" in btn.text.lower() or "save" in btn.text.lower():
                        btn.click()
                        published = True
                        print("📌 Publish button clicked (fallback)")
                        break
            
            if not published:
                print("⚠️ Could not find publish button")
                return False
            
            # Wait for success
            time.sleep(6)
            
            print(f"✅ Pin published successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Could not publish pin: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
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
    
    driver = None
    pin_path = None
    
    try:
        # Create pin image
        pin_path = f"temp_pin_{permalink}.png"
        create_pin_image(featured_image_path, hook_text, pin_path, style='modern')
        
        # Create driver
        driver = create_pinterest_driver()
        
        # Login
        if not login_to_pinterest(driver):
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
                print(f"🧹 Cleaned up temp file")
            except:
                pass
        
        if driver:
            try:
                driver.quit()
                print(f"🔚 Browser closed")
            except:
                pass


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