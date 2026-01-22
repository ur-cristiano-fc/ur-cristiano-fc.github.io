"""Pinterest automation using Selenium - Enhanced anti-detection"""
import os
import time
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from PIL import Image, ImageDraw, ImageFont
from article_generator import client, TEXT_MODEL

# Pinterest credentials
PINTEREST_EMAIL = os.environ.get("PINTEREST_EMAIL", "").strip()
PINTEREST_PASSWORD = os.environ.get("PINTEREST_PASSWORD", "").strip()
BLOG_SITE = "https://ur-cristiano-fc.github.io"

# Pin settings
PIN_WIDTH = 1000
PIN_HEIGHT = 1500


def generate_pin_variations(title, focus_kw):
    """Generate 3 unique pin variations using Gemini AI"""
    print(f"\n{'='*60}")
    print(f"🤖 AI: Generating 3 Unique Pinterest Pins")
    print(f"{'='*60}")
    
    prompt = f"""Create 3 different Pinterest pin variations for this article:
Title: "{title}"
Focus Keyword: "{focus_kw}"

For EACH of the 3 pins, create:
1. Title - Click-worthy, max 100 characters
2. Description - Engaging, includes keyword, max 400 characters  
3. Hook - Short punchy text for the pin image, max 8 words
4. Hashtags - 8-10 relevant tags with #

Return ONLY valid JSON array:
[
  {{"title": "...", "description": "...", "hook": "...", "hashtags": "..."}},
  {{"title": "...", "description": "...", "hook": "...", "hashtags": "..."}},
  {{"title": "...", "description": "...", "hook": "...", "hashtags": "..."}}
]"""
    
    try:
        response = client.models.generate_content(model=TEXT_MODEL, contents=prompt)
        text = response.text.strip()
        
        # Clean markdown
        if text.startswith('```json'):
            text = text.replace('```json', '').replace('```', '')
        elif text.startswith('```'):
            text = text.replace('```', '')
        
        text = text.strip()
        variations = json.loads(text)
        
        # Validate
        if len(variations) < 3:
            while len(variations) < 3:
                variations.append(variations[0])
        
        print(f"✅ Generated 3 unique pin variations")
        return variations[:3]
        
    except Exception as e:
        print(f"⚠️ AI generation failed, using fallbacks: {e}")
        
        return [
            {
                "title": title[:100],
                "description": f"Discover everything about {focus_kw}. Complete guide with expert insights.",
                "hook": f"Ultimate {focus_kw.title()} Guide",
                "hashtags": f"#{focus_kw.replace(' ', '')} #CristianoRonaldo #CR7 #Football"
            },
            {
                "title": f"Everything About {focus_kw.title()}",
                "description": f"Learn {focus_kw} secrets. {title}. Expert analysis and complete breakdown.",
                "hook": f"Master {focus_kw.title()}",
                "hashtags": f"#{focus_kw.replace(' ', '')} #CR7 #Ronaldo #SoccerTips"
            },
            {
                "title": f"{focus_kw.title()}: Complete Guide",
                "description": f"{title}. Everything you need to know about {focus_kw}.",
                "hook": f"{focus_kw.title()} Secrets",
                "hashtags": f"#{focus_kw.replace(' ', '')} #Football #CR7Facts"
            }
        ]


def create_pinterest_driver():
    """Create Selenium Chrome driver with enhanced anti-detection"""
    print("🚀 Initializing Chrome WebDriver...")
    
    chrome_options = Options()
    
    # Headless settings
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Enhanced anti-detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Realistic user agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    
    # Additional stealth
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    # Language and locale
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_experimental_option('prefs', {
        'intl.accept_languages': 'en-US,en'
    })
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Driver created successfully")
    except Exception as e:
        raise Exception(f"❌ Could not initialize Chrome: {e}")
    
    # Enhanced anti-detection scripts
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            // Overwrite the `navigator.webdriver` property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Overwrite the `navigator.plugins` property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Overwrite the `navigator.languages` property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Overwrite the `navigator.permissions` property
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock chrome runtime
            window.chrome = {
                runtime: {}
            };
        """
    })
    
    driver.set_page_load_timeout(60)
    return driver


def human_like_type(element, text, min_delay=0.05, max_delay=0.15):
    """Type text with random delays like a human"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))


def random_sleep(min_sec=1, max_sec=3):
    """Sleep for random duration"""
    time.sleep(random.uniform(min_sec, max_sec))


def set_react_input_value(driver, element, value):
    """Set value in React input fields"""
    driver.execute_script("""
        let input = arguments[0];
        let value = arguments[1];
        let lastValue = input.value;
        input.value = value;
        
        let event = new Event('input', { bubbles: true });
        event.simulated = true;
        
        let tracker = input._valueTracker;
        if (tracker) {
            tracker.setValue(lastValue);
        }
        
        input.dispatchEvent(event);
        input.dispatchEvent(new Event('change', { bubbles: true }));
    """, element, value)


def login_to_pinterest(driver):
    """Login to Pinterest with enhanced anti-detection"""
    try:
        print("\n🔐 Logging into Pinterest...")
        
        # Go to Pinterest homepage first (more natural)
        print("   📍 Loading Pinterest homepage...")
        driver.get("https://www.pinterest.com")
        random_sleep(3, 5)
        
        # Then go to login
        print("   📍 Navigating to login page...")
        driver.get("https://www.pinterest.com/login/")
        random_sleep(4, 6)
        
        # Take screenshot
        try:
            driver.save_screenshot("pinterest_login_page.png")
            print("   📸 Login page screenshot saved")
        except:
            pass
        
        # Wait for email input
        print("   ⏳ Waiting for login form...")
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        random_sleep(1, 2)
        
        # Click email input
        print("   📧 Entering email...")
        email_input.click()
        random_sleep(0.5, 1)
        
        # Type email like human
        human_like_type(email_input, PINTEREST_EMAIL)
        print(f"   ✅ Email entered: {PINTEREST_EMAIL}")
        random_sleep(1, 2)
        
        # Find password input
        password_input = driver.find_element(By.ID, "password")
        password_input.click()
        random_sleep(0.5, 1)
        
        # Type password like human
        print("   🔑 Entering password...")
        human_like_type(password_input, PINTEREST_PASSWORD)
        print("   ✅ Password entered")
        random_sleep(1, 2)
        
        # Take screenshot before submit
        try:
            driver.save_screenshot("pinterest_before_submit.png")
        except:
            pass
        
        # Submit login
        try:
            login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            print("   🔘 Clicking login button...")
            login_btn.click()
        except:
            print("   🔘 Pressing Enter...")
            password_input.send_keys(Keys.ENTER)
        
        print("   ⏳ Waiting for login to complete...")
        random_sleep(10, 15)
        
        # Take screenshot after submit
        try:
            driver.save_screenshot("pinterest_after_submit.png")
        except:
            pass
        
        # Check current URL
        current_url = driver.current_url
        print(f"   📍 Current URL: {current_url}")
        
        # Check if still on login page
        if "login" in current_url.lower():
            print("❌ Login failed - still on login page")
            
            # Check for error messages
            try:
                page_source = driver.page_source
                if "captcha" in page_source.lower():
                    print("   🤖 CAPTCHA detected - Pinterest blocked the login")
                elif "incorrect" in page_source.lower() or "wrong" in page_source.lower():
                    print("   ❌ Incorrect credentials")
                else:
                    print("   ⚠️ Unknown login issue")
            except:
                pass
            
            return False
        
        # Additional check - look for user menu
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='header-profile']"))
            )
            print("✅ Logged in successfully - user menu found")
            return True
        except:
            print("⚠️ Login may have succeeded but user menu not found")
            # Proceed anyway if we're not on login page
            return "login" not in current_url.lower()
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            driver.save_screenshot("pinterest_login_error.png")
        except:
            pass
        
        return False


def create_pin_image(base_image_path, hook_text, output_path, variation_idx=0):
    """Create Pinterest pin image"""
    try:
        base_img = Image.open(base_image_path).convert('RGB')
        pin = Image.new('RGB', (PIN_WIDTH, PIN_HEIGHT), (255, 255, 255))
        
        # Image area (top 60%)
        img_height = int(PIN_HEIGHT * 0.6)
        aspect_ratio = base_img.height / base_img.width
        new_width = PIN_WIDTH
        new_height = int(new_width * aspect_ratio)
        
        if new_height > img_height:
            new_height = img_height
            new_width = int(new_height / aspect_ratio)
        
        base_img = base_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        pin.paste(base_img, ((PIN_WIDTH - new_width) // 2, 0))
        
        # Text area
        draw = ImageDraw.Draw(pin)
        
        # Color schemes
        color_schemes = [
            {'bg': (45, 52, 54), 'text': (255, 255, 255), 'accent': (255, 71, 87)},
            {'bg': (255, 71, 87), 'text': (255, 255, 255), 'accent': (45, 52, 54)},
            {'bg': (9, 132, 227), 'text': (255, 255, 255), 'accent': (255, 255, 255)}
        ]
        
        colors = color_schemes[variation_idx % 3]
        
        # Background
        draw.rectangle([(0, img_height), (PIN_WIDTH, PIN_HEIGHT)], fill=colors['bg'])
        draw.rectangle([(0, img_height), (PIN_WIDTH, img_height + 10)], fill=colors['accent'])
        
        # Font
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            url_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            title_font = ImageFont.load_default()
            url_font = ImageFont.load_default()
        
        # Word wrap hook text
        words = hook_text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), test_line, font=title_font)
            if bbox[2] - bbox[0] > PIN_WIDTH - 100:
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw text
        y_position = img_height + 80
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_width = bbox[2] - bbox[0]
            x = (PIN_WIDTH - text_width) // 2
            draw.text((x, y_position), line, font=title_font, fill=colors['text'])
            y_position += bbox[3] - bbox[1] + 20
        
        # URL
        url_text = "ur-cristiano-fc.github.io"
        bbox = draw.textbbox((0, 0), url_text, font=url_font)
        text_width = bbox[2] - bbox[0]
        x = (PIN_WIDTH - text_width) // 2
        y = PIN_HEIGHT - 80
        draw.text((x, y), url_text, font=url_font, fill=colors['accent'])
        
        pin.save(output_path, 'PNG', quality=95)
        print(f"   ✅ Pin image created: {os.path.getsize(output_path)/1024:.1f} KB")
        
        return output_path
        
    except Exception as e:
        print(f"   ❌ Image creation failed: {e}")
        return None


def upload_pin_to_pinterest(driver, image_path, title, description, link):
    """Upload single pin to Pinterest"""
    try:
        print(f"\n   📤 Uploading pin...")
        
        driver.get("https://www.pinterest.com/pin-builder/")
        random_sleep(5, 7)
        
        # Dismiss popups
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            random_sleep(1, 2)
        except:
            pass
        
        # Upload image
        print(f"      📸 Uploading image...")
        file_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        file_input.send_keys(os.path.abspath(image_path))
        random_sleep(7, 10)
        print(f"      ✅ Image uploaded")
        
        # Enter title
        try:
            print(f"      ✏️ Entering title...")
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='pin-draft-title']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", title_input)
            random_sleep(1, 2)
            
            title_input.click()
            random_sleep(0.5, 1)
            set_react_input_value(driver, title_input, title[:100])
            random_sleep(1, 2)
            print(f"      ✅ Title entered")
        except Exception as e:
            print(f"      ⚠️ Title: {e}")
        
        # Enter description
        try:
            print(f"      ✏️ Entering description...")
            desc_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-description']")
            driver.execute_script("arguments[0].scrollIntoView(true);", desc_input)
            random_sleep(1, 2)
            
            desc_input.click()
            random_sleep(0.5, 1)
            set_react_input_value(driver, desc_input, description[:500])
            random_sleep(1, 2)
            print(f"      ✅ Description entered")
        except Exception as e:
            print(f"      ⚠️ Description: {e}")
        
        # Enter link
        try:
            print(f"      🔗 Adding link...")
            link_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-link']")
            driver.execute_script("arguments[0].scrollIntoView(true);", link_input)
            random_sleep(1, 2)
            
            link_input.click()
            random_sleep(0.5, 1)
            set_react_input_value(driver, link_input, link)
            random_sleep(1, 2)
            print(f"      ✅ Link added")
        except Exception as e:
            print(f"      ⚠️ Link: {e}")
        
        # Select board
        try:
            print(f"      📋 Selecting board...")
            board_btn = driver.find_element(By.CSS_SELECTOR, "[data-test-id='board-dropdown-select-button']")
            board_btn.click()
            random_sleep(2, 3)
            
            first_board = driver.find_element(By.CSS_SELECTOR, "[data-test-id='board-row']")
            first_board.click()
            random_sleep(2, 3)
            print(f"      ✅ Board selected")
        except Exception as e:
            print(f"      ⚠️ Board: {e}")
        
        # Publish
        try:
            print(f"      🚀 Publishing...")
            publish_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test-id='board-dropdown-save-button']"))
            )
            publish_btn.click()
            random_sleep(8, 12)
            print(f"      ✅ Pin published!")
            return True
        except Exception as e:
            print(f"      ❌ Publish failed: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return False


def post_to_pinterest_selenium(title, focus_kw, permalink, featured_image_path, description, hook_text):
    """Main function - Creates and posts 3 unique pins"""
    
    if not PINTEREST_EMAIL or not PINTEREST_PASSWORD:
        print("❌ Pinterest credentials not found")
        return False
    
    print(f"\n{'='*60}")
    print(f"📌 Pinterest Auto-Poster: 3 Unique Pins")
    print(f"{'='*60}")
    
    # Generate variations
    variations = generate_pin_variations(title, focus_kw)
    
    driver = None
    success_count = 0
    pin_files = []
    
    try:
        driver = create_pinterest_driver()
        
        if not login_to_pinterest(driver):
            print("❌ Login failed - check credentials or CAPTCHA blocking")
            print("💡 Try:")
            print("   1. Verify PINTEREST_EMAIL and PINTEREST_PASSWORD are correct")
            print("   2. Login manually to Pinterest once to bypass CAPTCHA")
            print("   3. Use Pinterest API instead of Selenium")
            return False
        
        article_url = f"{BLOG_SITE}/{permalink}"
        
        # Upload each pin
        for i, pin_data in enumerate(variations):
            print(f"\n{'='*60}")
            print(f"📌 Pin {i+1}/3")
            print(f"{'='*60}")
            
            pin_path = f"temp_pin_{i}_{permalink}.png"
            pin_files.append(pin_path)
            
            if not create_pin_image(featured_image_path, pin_data['hook'], pin_path, i):
                continue
            
            full_description = f"{pin_data['description']}\n\n{pin_data['hashtags']}"
            
            if upload_pin_to_pinterest(driver, pin_path, pin_data['title'], full_description, article_url):
                success_count += 1
            
            if i < len(variations) - 1:
                print(f"   ⏳ Waiting before next pin...")
                random_sleep(12, 18)
        
        print(f"\n{'='*60}")
        print(f"📊 Complete: {success_count}/3 pins posted")
        print(f"{'='*60}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        for pin_file in pin_files:
            if os.path.exists(pin_file):
                try:
                    os.remove(pin_file)
                except:
                    pass
        
        if driver:
            try:
                driver.quit()
            except:
                pass


if __name__ == "__main__":
    post_to_pinterest_selenium(
        title="Test Article",
        focus_kw="test keyword",
        permalink="test-permalink",
        featured_image_path="assets/images/test.webp",
        description="Test description",
        hook_text="Test Hook"
    )