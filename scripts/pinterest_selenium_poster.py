"""Pinterest automation using Selenium with Gemini AI Content Generation"""
import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont
from article_generator import client, TEXT_MODEL  # Import Gemini client

# Pinterest credentials
PINTEREST_EMAIL = os.environ.get("PINTEREST_EMAIL")
PINTEREST_PASSWORD = os.environ.get("PINTEREST_PASSWORD")
BLOG_SITE = "https://ur-cristiano-fc.github.io"

# Pin settings
PIN_WIDTH = 1000
PIN_HEIGHT = 1500


def generate_pin_variations(title, focus_kw):
    """Generate 3 unique pin variations using Gemini AI"""
    print(f"🤖 Generating 3 unique Pinterest pins for: {title}")
    
    prompt = f"""
    I need 3 different Pinterest pin variations for a blog post titled "{title}".
    Focus Keyword: "{focus_kw}"

    For EACH of the 3 pins, provide:
    1. A click-worthy Title (max 100 chars)
    2. An engaging Description (max 400 chars)
    3. A short, punchy "Hook Text" to put on the image (max 6 words)
    4. Relevant Hashtags (8-10 tags)

    STRICT JSON FORMAT ONLY. No markdown, no "here is the json".
    Return a list of 3 objects exactly like this:
    [
      {{
        "title": "Pin 1 Title Here",
        "description": "Pin 1 description...",
        "hook": "Hook Text 1",
        "hashtags": "#tag1 #tag2"
      }},
      ...
    ]
    """

    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt
        )
        
        # Clean response text to ensure valid JSON
        text = response.text.strip()
        if text.startswith('```json'):
            text = text.replace('```json', '').replace('```', '')
        elif text.startswith('```'):
            text = text.replace('```', '')
            
        variations = json.loads(text)
        print(f"✅ Generated {len(variations)} pin variations")
        return variations
        
    except Exception as e:
        print(f"⚠️ AI generation failed: {e}")
        # Fallback data
        return [
            {
                "title": title[:100],
                "description": f"Read more about {title}. {focus_kw} explained!",
                "hook": title[:30],
                "hashtags": f"#{focus_kw.replace(' ', '')}"
            }
        ] * 3


def create_pinterest_driver():
    """Create Selenium Chrome driver with proper configuration"""
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
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
    except Exception as e:
        print(f"⚠️ Webdriver-manager failed: {e}. using fallback...")
        driver = webdriver.Chrome(options=chrome_options)
    
    return driver


def login_to_pinterest(driver):
    """Login to Pinterest"""
    try:
        print("🔐 Logging into Pinterest...")
        driver.get("[https://www.pinterest.com/login/](https://www.pinterest.com/login/)")
        time.sleep(5)
        
        # Email
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_input.clear()
        email_input.send_keys(PINTEREST_EMAIL)
        time.sleep(2)
        
        # Password
        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys(PINTEREST_PASSWORD)
        time.sleep(2)
        
        # Login Button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        print("🔘 Login button clicked")
        
        time.sleep(15)
        
        if "login" in driver.current_url:
            print("❌ Login failed")
            return False
            
        print("✅ Logged in successfully")
        return True
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return False


def create_pin_image(base_image_path, hook_text, output_path, variation_idx=0):
    """Create pin image with varied designs"""
    print(f"🎨 Creating Pin {variation_idx + 1} Image...")
    
    try:
        base_img = Image.open(base_image_path).convert('RGB')
        pin = Image.new('RGB', (PIN_WIDTH, PIN_HEIGHT), (255, 255, 255))
        
        # Design variations (Top 60% image)
        img_height = int(PIN_HEIGHT * 0.6)
        
        # Resize logic
        aspect_ratio = base_img.height / base_img.width
        new_width = PIN_WIDTH
        new_height = int(new_width * aspect_ratio)
        if new_height > img_height:
            new_height = img_height
            new_width = int(new_height / aspect_ratio)
        
        base_img = base_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        x_offset = (PIN_WIDTH - new_width) // 2
        pin.paste(base_img, (x_offset, 0))
        
        draw = ImageDraw.Draw(pin)
        
        # Varied Background Colors for Text Area
        colors = [(45, 52, 54), (255, 71, 87), (9, 132, 227)] # Grey, Red, Blue
        bg_color = colors[variation_idx % len(colors)]
        
        draw.rectangle([(0, img_height), (PIN_WIDTH, PIN_HEIGHT)], fill=bg_color)
        
        # Font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        except:
            font = ImageFont.load_default()

        # Wrap Hook Text
        text_y = img_height + 120
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
                text_y += 90
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
    """Upload a single pin"""
    try:
        print(f"   📤 Opening Pin Builder...")
        driver.get("[https://www.pinterest.com/pin-builder/](https://www.pinterest.com/pin-builder/)")
        time.sleep(8)
        
        # 0. Close Popups (Welcome/Cookies)
        try:
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except:
            pass

        # 1. Upload Image
        try:
            file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(os.path.abspath(image_path))
            print("   📸 Image uploaded")
            time.sleep(8) # Wait for processing
        except Exception as e:
            print(f"   ❌ Image upload failed: {e}")
            return False

        # 2. Enter Title (Smart Selectors)
        title_selectors = [
            "[data-test-id='pin-draft-title']",
            "[data-test-id='pin-title-input']",
            "input[aria-label='Add your title']",
            "textarea[aria-label='Add your title']",
            "input[type='text']" # Fallback
        ]
        
        title_entered = False
        for selector in title_selectors:
            try:
                title_input = driver.find_element(By.CSS_SELECTOR, selector)
                # Ensure it's the right one (sometimes multiple inputs exist)
                if title_input.is_displayed():
                    driver.execute_script("arguments[0].click();", title_input)
                    title_input.clear()
                    title_input.send_keys(title[:100])
                    print(f"   ✏️ Title entered")
                    title_entered = True
                    break
            except:
                continue
        
        if not title_entered:
            print("   ❌ Title entry failed (Selectors exhausted)")
            driver.save_screenshot("debug_title_failed.png")
            return False

        # 3. Enter Description
        try:
            desc_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-description']")
            driver.execute_script("arguments[0].click();", desc_input)
            desc_input.send_keys(description[:500])
            print("   ✏️ Description entered")
        except:
            print("   ⚠️ Description skipped")

        # 4. Enter Link
        try:
            link_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-link']")
            driver.execute_script("arguments[0].click();", link_input)
            link_input.send_keys(link)
            print("   🔗 Link added")
        except:
            print("   ⚠️ Link skipped")

        # 5. Select Board
        try:
            board_dropdown = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test-id='board-dropdown-select-button']"))
            )
            board_dropdown.click()
            time.sleep(2)
            
            first_board = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test-id='board-row-item']"))
            )
            first_board.click()
            print("   ✅ Board selected")
        except:
            print("   ❌ Board selection failed")
            return False

        # 6. Publish
        try:
            save_btn = driver.find_element(By.CSS_SELECTOR, "[data-test-id='board-dropdown-save-button']")
            save_btn.click()
            print("   🚀 Publish button clicked")
            time.sleep(10)
            return True
        except:
            print("   ❌ Publish click failed")
            return False

    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return False


def post_to_pinterest_selenium(title, focus_kw, permalink, featured_image_path, description, hook_text):
    """Main function called by generate_posts.py"""
    
    if not PINTEREST_EMAIL or not PINTEREST_PASSWORD:
        print("❌ Credentials missing")
        return False
        
    # 1. Generate 3 Pin Variations using Gemini
    variations = generate_pin_variations(title, focus_kw)
    
    driver = create_pinterest_driver()
    if not login_to_pinterest(driver):
        driver.quit()
        return False
        
    success_count = 0
    article_url = f"{BLOG_SITE}/{permalink}"
    
    # 2. Loop through variations and post
    try:
        for i, pin_data in enumerate(variations):
            print(f"\n📌 Processing Pin {i+1}/3")
            
            # Create unique image
            pin_img_path = f"temp_pin_{i}_{permalink}.png"
            create_pin_image(featured_image_path, pin_data['hook'], pin_img_path, i)
            
            # Construct full description with hashtags
            full_desc = f"{pin_data['description']}\n\n{pin_data['hashtags']}"
            
            # Upload
            if upload_pin_to_pinterest(driver, pin_img_path, pin_data['title'], full_desc, article_url):
                print(f"✅ Pin {i+1} Posted Successfully!")
                success_count += 1
            else:
                print(f"❌ Pin {i+1} Failed")
            
            # Cleanup image
            if os.path.exists(pin_img_path):
                os.remove(pin_img_path)
            
            # Wait random time before next pin
            if i < len(variations) - 1:
                wait_time = 10
                print(f"⏳ Waiting {wait_time}s before next pin...")
                time.sleep(wait_time)
                
    except Exception as e:
        print(f"❌ Loop Error: {e}")
        
    finally:
        driver.quit()
        
    print(f"\n📊 Pinterest Run Complete: {success_count}/{len(variations)} posted")
    return success_count > 0