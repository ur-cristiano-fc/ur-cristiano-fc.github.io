"""Pinterest automation using Selenium - Creates 3 unique pins per article"""
import os
import time
import json
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
    print(f"Article: {title[:60]}...")
    
    prompt = f"""Create 3 different Pinterest pin variations for this article:
Title: "{title}"
Focus Keyword: "{focus_kw}"

For EACH of the 3 pins, create:
1. Title - Click-worthy, max 100 characters
2. Description - Engaging, includes keyword, max 400 characters  
3. Hook - Short punchy text for the pin image, max 8 words
4. Hashtags - 8-10 relevant tags with #

Return ONLY valid JSON array with no markdown:
[
  {{
    "title": "Pin 1 Title Here",
    "description": "Pin 1 description with keyword...",
    "hook": "Short Hook Text",
    "hashtags": "#tag1 #tag2 #tag3"
  }},
  {{
    "title": "Pin 2 Title Here", 
    "description": "Pin 2 description...",
    "hook": "Different Hook",
    "hashtags": "#tag1 #tag2"
  }},
  {{
    "title": "Pin 3 Title Here",
    "description": "Pin 3 description...", 
    "hook": "Another Hook",
    "hashtags": "#tag1 #tag2"
  }}
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
        
        # Validate we got 3 pins
        if len(variations) < 3:
            print(f"⚠️ AI returned {len(variations)} pins, using fallback for missing ones")
            while len(variations) < 3:
                variations.append(variations[0])
        
        print(f"✅ Generated 3 unique pin variations:")
        for i, pin in enumerate(variations[:3], 1):
            print(f"   Pin {i}: {pin['title'][:50]}...")
            print(f"           Hook: {pin['hook']}")
        
        return variations[:3]
        
    except Exception as e:
        print(f"⚠️ AI generation failed: {e}")
        print(f"📝 Using fallback variations")
        
        # Fallback variations
        return [
            {
                "title": title[:100],
                "description": f"Discover everything about {focus_kw}. Complete guide with expert insights and tips. {title}",
                "hook": f"Ultimate {focus_kw.title()} Guide",
                "hashtags": f"#{focus_kw.replace(' ', '')} #CristianoRonaldo #CR7 #Football #Soccer"
            },
            {
                "title": f"Everything About {focus_kw.title()}",
                "description": f"Learn {focus_kw} secrets. {title}. Expert analysis and complete breakdown.",
                "hook": f"Master {focus_kw.title()}",
                "hashtags": f"#{focus_kw.replace(' ', '')} #CR7 #Ronaldo #SoccerTips"
            },
            {
                "title": f"{focus_kw.title()}: Complete Guide",
                "description": f"{title}. Everything you need to know about {focus_kw}. Click to read more!",
                "hook": f"{focus_kw.title()} Secrets",
                "hashtags": f"#{focus_kw.replace(' ', '')} #Football #CR7Facts"
            }
        ]


def create_pinterest_driver():
    """Create Selenium Chrome driver - FIXED for GitHub Actions"""
    print("🚀 Initializing Chrome WebDriver...")
    
    chrome_options = Options()
    
    # Critical headless settings
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Anti-detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Additional stability
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--ignore-certificate-errors")
    
    try:
        # Try with explicit chromedriver path
        service = Service('/usr/local/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Driver created with /usr/local/bin/chromedriver")
    except Exception as e:
        print(f"⚠️ Failed with explicit path: {e}")
        try:
            # Try default
            driver = webdriver.Chrome(options=chrome_options)
            print("✅ Driver created with default chromedriver")
        except Exception as e2:
            raise Exception(f"❌ Could not initialize Chrome: {e2}")
    
    # Anti-detection script
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        """
    })
    
    driver.set_page_load_timeout(60)
    return driver


def set_react_input_value(driver, element, value):
    """Set value in React input fields and trigger change events"""
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
    """Login to Pinterest"""
    try:
        print("\n🔐 Logging into Pinterest...")
        driver.get("https://www.pinterest.com/login/")
        time.sleep(5)
        
        # Email
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_input.clear()
        time.sleep(0.5)
        email_input.send_keys(PINTEREST_EMAIL)
        print(f"   ✅ Email entered: {PINTEREST_EMAIL}")
        time.sleep(1.5)
        
        # Password
        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        time.sleep(0.5)
        password_input.send_keys(PINTEREST_PASSWORD)
        print(f"   ✅ Password entered")
        time.sleep(1.5)
        
        # Submit
        try:
            login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
        except:
            password_input.send_keys(Keys.ENTER)
        
        print("   🔘 Login submitted")
        time.sleep(12)
        
        # Check if logged in
        if "login" in driver.current_url.lower():
            print("❌ Login failed - still on login page")
            try:
                driver.save_screenshot("pinterest_login_failed.png")
            except:
                pass
            return False
        
        print("✅ Logged in successfully")
        return True
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_pin_image(base_image_path, hook_text, output_path, variation_idx=0):
    """Create Pinterest pin image with hook text overlay"""
    try:
        print(f"   🎨 Creating pin image #{variation_idx + 1}...")
        
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
        
        # Different color schemes for each variation
        color_schemes = [
            {'bg': (45, 52, 54), 'text': (255, 255, 255), 'accent': (255, 71, 87)},      # Dark
            {'bg': (255, 71, 87), 'text': (255, 255, 255), 'accent': (45, 52, 54)},      # Red
            {'bg': (9, 132, 227), 'text': (255, 255, 255), 'accent': (255, 255, 255)}    # Blue
        ]
        
        colors = color_schemes[variation_idx % 3]
        
        # Draw text background
        text_area_y = img_height
        draw.rectangle([(0, text_area_y), (PIN_WIDTH, PIN_HEIGHT)], fill=colors['bg'])
        
        # Accent bar
        draw.rectangle([(0, text_area_y), (PIN_WIDTH, text_area_y + 10)], fill=colors['accent'])
        
        # Load font
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            url_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            title_font = ImageFont.load_default()
            url_font = ImageFont.load_default()
        
        # Draw hook text (word wrap)
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
        
        # Draw lines
        y_position = text_area_y + 80
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_width = bbox[2] - bbox[0]
            x = (PIN_WIDTH - text_width) // 2
            draw.text((x, y_position), line, font=title_font, fill=colors['text'])
            y_position += bbox[3] - bbox[1] + 20
        
        # Draw URL
        url_text = "ur-cristiano-fc.github.io"
        bbox = draw.textbbox((0, 0), url_text, font=url_font)
        text_width = bbox[2] - bbox[0]
        x = (PIN_WIDTH - text_width) // 2
        y = PIN_HEIGHT - 80
        draw.text((x, y), url_text, font=url_font, fill=colors['accent'])
        
        # Save
        pin.save(output_path, 'PNG', quality=95)
        file_size = os.path.getsize(output_path)
        print(f"   ✅ Pin image created: {output_path} ({file_size/1024:.1f} KB)")
        
        return output_path
        
    except Exception as e:
        print(f"   ❌ Image creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def upload_pin_to_pinterest(driver, image_path, title, description, link):
    """Upload single pin to Pinterest"""
    try:
        print(f"\n   📤 Uploading to Pinterest...")
        print(f"      Title: {title[:50]}...")
        
        # Go to pin builder
        driver.get("https://www.pinterest.com/pin-builder/")
        time.sleep(6)
        
        # Dismiss any popups
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
        except:
            pass
        
        # Upload image
        print(f"      📸 Uploading image...")
        file_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        file_input.send_keys(os.path.abspath(image_path))
        time.sleep(8)
        print(f"      ✅ Image uploaded")
        
        # Enter title
        try:
            print(f"      ✏️ Entering title...")
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='pin-draft-title']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", title_input)
            time.sleep(1)
            
            # Try React method
            set_react_input_value(driver, title_input, title[:100])
            time.sleep(1)
            
            # Fallback: standard input
            title_input.click()
            title_input.clear()
            title_input.send_keys(title[:100])
            print(f"      ✅ Title entered")
        except Exception as e:
            print(f"      ⚠️ Title entry warning: {e}")
        
        # Enter description
        try:
            print(f"      ✏️ Entering description...")
            desc_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-description']")
            driver.execute_script("arguments[0].scrollIntoView(true);", desc_input)
            time.sleep(1)
            
            set_react_input_value(driver, desc_input, description[:500])
            time.sleep(1)
            
            desc_input.click()
            desc_input.send_keys(description[:500])
            print(f"      ✅ Description entered")
        except Exception as e:
            print(f"      ⚠️ Description entry warning: {e}")
        
        # Enter link
        try:
            print(f"      🔗 Adding link...")
            link_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-link']")
            driver.execute_script("arguments[0].scrollIntoView(true);", link_input)
            time.sleep(1)
            
            set_react_input_value(driver, link_input, link)
            time.sleep(1)
            
            link_input.click()
            link_input.send_keys(link)
            print(f"      ✅ Link added: {link}")
        except Exception as e:
            print(f"      ⚠️ Link entry warning: {e}")
        
        # Select board
        try:
            print(f"      📋 Selecting board...")
            board_btn = driver.find_element(By.CSS_SELECTOR, "[data-test-id='board-dropdown-select-button']")
            board_btn.click()
            time.sleep(3)
            
            # Select first board
            first_board = driver.find_element(By.CSS_SELECTOR, "[data-test-id='board-row']")
            first_board.click()
            time.sleep(2)
            print(f"      ✅ Board selected")
        except Exception as e:
            print(f"      ⚠️ Board selection warning: {e}")
        
        # Publish
        try:
            print(f"      🚀 Publishing pin...")
            publish_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test-id='board-dropdown-save-button']"))
            )
            publish_btn.click()
            time.sleep(10)
            print(f"      ✅ Pin published!")
            return True
        except Exception as e:
            print(f"      ❌ Publish failed: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def post_to_pinterest_selenium(title, focus_kw, permalink, featured_image_path, description, hook_text):
    """Main function - Creates and posts 3 unique pins to Pinterest"""
    
    if not PINTEREST_EMAIL or not PINTEREST_PASSWORD:
        print("❌ Pinterest credentials not found")
        return False
    
    print(f"\n{'='*60}")
    print(f"📌 Pinterest Auto-Poster: 3 Unique Pins")
    print(f"{'='*60}")
    print(f"Article: {title[:60]}...")
    print(f"Email: {PINTEREST_EMAIL}")
    
    # Step 1: Generate 3 unique pin variations with AI
    variations = generate_pin_variations(title, focus_kw)
    
    # Step 2: Create driver and login
    driver = None
    success_count = 0
    pin_files = []
    
    try:
        driver = create_pinterest_driver()
        
        if not login_to_pinterest(driver):
            print("❌ Login failed, cannot proceed")
            return False
        
        article_url = f"{BLOG_SITE}/{permalink}"
        
        # Step 3: Create and upload each pin
        for i, pin_data in enumerate(variations):
            print(f"\n{'='*60}")
            print(f"📌 Processing Pin {i+1}/3")
            print(f"{'='*60}")
            
            # Create unique pin image
            pin_path = f"temp_pin_{i}_{permalink}.png"
            pin_files.append(pin_path)
            
            image_created = create_pin_image(
                featured_image_path,
                pin_data['hook'],
                pin_path,
                variation_idx=i
            )
            
            if not image_created:
                print(f"   ⚠️ Skipping pin {i+1} - image creation failed")
                continue
            
            # Upload pin
            full_description = f"{pin_data['description']}\n\n{pin_data['hashtags']}"
            
            if upload_pin_to_pinterest(
                driver,
                pin_path,
                pin_data['title'],
                full_description,
                article_url
            ):
                success_count += 1
                print(f"   ✅ Pin {i+1}/3 posted successfully!")
            else:
                print(f"   ❌ Pin {i+1}/3 failed to post")
            
            # Wait between pins
            if i < len(variations) - 1:
                print(f"   ⏳ Waiting 15 seconds before next pin...")
                time.sleep(15)
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 Pinterest Posting Complete")
        print(f"{'='*60}")
        print(f"✅ Successfully posted: {success_count}/3 pins")
        print(f"❌ Failed: {3 - success_count}/3 pins")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        for pin_file in pin_files:
            if os.path.exists(pin_file):
                try:
                    os.remove(pin_file)
                    print(f"🧹 Cleaned up: {pin_file}")
                except:
                    pass
        
        if driver:
            try:
                driver.quit()
                print(f"🔚 Browser closed")
            except:
                pass


# Test
if __name__ == "__main__":
    post_to_pinterest_selenium(
        title="Cristiano Ronaldo Training Secrets",
        focus_kw="cristiano ronaldo training",
        permalink="cristiano-training-secrets",
        featured_image_path="assets/images/featured_test.webp",
        description="Discover CR7's workout routine",
        hook_text="Ultimate Training Guide"
    )