"""Pinterest automation using Selenium with Robust React Input Handling"""
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
from PIL import Image, ImageDraw, ImageFont
from article_generator import client, TEXT_MODEL

# Pinterest credentials (Sanitized)
PINTEREST_EMAIL = str(os.environ.get("PINTEREST_EMAIL", "")).strip()
PINTEREST_PASSWORD = str(os.environ.get("PINTEREST_PASSWORD", "")).strip()
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

    STRICT JSON FORMAT ONLY. No markdown. Return a list of 3 objects:
    [
      {{
        "title": "Pin 1 Title",
        "description": "Pin 1 description...",
        "hook": "Hook Text 1",
        "hashtags": "#tag1"
      }}
    ]
    """
    try:
        response = client.models.generate_content(model=TEXT_MODEL, contents=prompt)
        text = response.text.strip()
        if text.startswith('```json'): text = text.replace('```json', '').replace('```', '')
        elif text.startswith('```'): text = text.replace('```', '')
        return json.loads(text)
    except:
        return [{
            "title": title[:100],
            "description": f"{title}. {focus_kw} full guide.",
            "hook": title[:30],
            "hashtags": f"#{focus_kw.replace(' ', '')}"
        }] * 3

def create_pinterest_driver():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    return driver

def set_native_value(driver, element, value):
    """React hack: Set value and dispatch input events so the 'Save' button enables"""
    driver.execute_script("""
        let input = arguments[0];
        let lastValue = input.value;
        input.value = arguments[1];
        let event = new Event('input', { bubbles: true });
        event.simulated = true;
        let tracker = input._valueTracker;
        if (tracker) { tracker.setValue(lastValue); }
        input.dispatchEvent(event);
    """, element, value)

def login_to_pinterest(driver):
    try:
        print("🔐 Logging into Pinterest...")
        driver.get("[https://www.pinterest.com/login/](https://www.pinterest.com/login/)")
        time.sleep(5)
        
        # Email
        email_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "email")))
        email_input.clear()
        email_input.send_keys(PINTEREST_EMAIL)
        time.sleep(1)
        
        # Password
        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys(PINTEREST_PASSWORD)
        time.sleep(1)
        
        # Click Login
        try:
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        except:
            password_input.send_keys(Keys.ENTER)
            
        print("🔘 Login submitted")
        time.sleep(10)
        
        if "login" in driver.current_url:
            print("❌ Login failed (Still on login page)")
            return False
            
        print("✅ Logged in successfully")
        return True
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return False

def create_pin_image(base_image_path, hook_text, output_path, variation_idx=0):
    try:
        base_img = Image.open(base_image_path).convert('RGB')
        pin = Image.new('RGB', (PIN_WIDTH, PIN_HEIGHT), (255, 255, 255))
        img_height = int(PIN_HEIGHT * 0.6)
        
        # Resize logic
        aspect_ratio = base_img.height / base_img.width
        new_width = PIN_WIDTH
        new_height = int(new_width * aspect_ratio)
        if new_height > img_height:
            new_height = img_height
            new_width = int(new_height / aspect_ratio)
        
        base_img = base_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        pin.paste(base_img, ((PIN_WIDTH - new_width) // 2, 0))
        
        draw = ImageDraw.Draw(pin)
        colors = [(45, 52, 54), (255, 71, 87), (9, 132, 227)]
        draw.rectangle([(0, img_height), (PIN_WIDTH, PIN_HEIGHT)], fill=colors[variation_idx % 3])
        
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        except: font = ImageFont.load_default()

        # Text Wrap
        y, lines = img_height + 120, []
        for word in hook_text.split():
            lines.append(word)
            if draw.textbbox((0, 0), ' '.join(lines), font=font)[2] > PIN_WIDTH - 100:
                lines.pop()
                text = ' '.join(lines)
                w = draw.textbbox((0, 0), text, font=font)[2]
                draw.text(((PIN_WIDTH - w) // 2, y), text, font=font, fill="white")
                y += 90
                lines = [word]
        if lines:
            text = ' '.join(lines)
            w = draw.textbbox((0, 0), text, font=font)[2]
            draw.text(((PIN_WIDTH - w) // 2, y), text, font=font, fill="white")

        pin.save(output_path, 'PNG')
        return output_path
    except Exception as e:
        print(f"⚠️ Image creation failed: {e}")
        return None

def upload_pin_to_pinterest(driver, image_path, title, description, link):
    try:
        print(f"   📤 Opening Pin Builder...")
        driver.get("[https://www.pinterest.com/pin-builder/](https://www.pinterest.com/pin-builder/)")
        time.sleep(8)
        
        # Dismiss popups
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()

        # 1. Upload
        driver.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(os.path.abspath(image_path))
        print("   📸 Image uploaded")
        time.sleep(5)

        # 2. Enter Title (Robust Method)
        print("   ✏️ Entering Title...")
        title_selectors = ["[data-test-id='pin-draft-title']", "[data-test-id='pin-title-input']", "input[type='text']"]
        title_found = False
        
        for selector in title_selectors:
            try:
                inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                for inp in inputs:
                    if inp.is_displayed():
                        # Try standard click & type
                        driver.execute_script("arguments[0].click();", inp)
                        inp.clear()
                        inp.send_keys(title[:100])
                        # Try React Hack
                        set_native_value(driver, inp, title[:100])
                        title_found = True
                        break
                if title_found: break
            except: continue
        
        if not title_found:
            print("   ⚠️ Could not find Title input via selectors. Trying Tab navigation...")
            actions = ActionChains(driver)
            actions.send_keys(Keys.TAB).send_keys(title[:100]).perform()

        # 3. Enter Description
        try:
            desc_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-description']")
            driver.execute_script("arguments[0].click();", desc_input)
            set_native_value(driver, desc_input, description[:500])
            print("   ✏️ Description entered")
        except: pass

        # 4. Enter Link
        try:
            link_input = driver.find_element(By.CSS_SELECTOR, "[data-test-id='pin-draft-link']")
            driver.execute_script("arguments[0].click();", link_input)
            set_native_value(driver, link_input, link)
            print("   🔗 Link added")
        except: pass

        # 5. Select Board
        try:
            print("   📋 Selecting Board...")
            driver.find_element(By.CSS_SELECTOR, "[data-test-id='board-dropdown-select-button']").click()
            time.sleep(2)
            driver.find_element(By.CSS_SELECTOR, "[data-test-id='board-row-item']").click()
        except:
            print("   ❌ Board selection failed")
            return False

        # 6. Publish
        try:
            time.sleep(2)
            driver.find_element(By.CSS_SELECTOR, "[data-test-id='board-dropdown-save-button']").click()
            print("   🚀 Published!")
            time.sleep(8)
            return True
        except Exception as e:
            print(f"   ❌ Publish Click Failed: {e}")
            return False

    except Exception as e:
        print(f"   ❌ Upload flow failed: {e}")
        return False

def post_to_pinterest_selenium(title, focus_kw, permalink, featured_image_path, description, hook_text):
    if not PINTEREST_EMAIL or not PINTEREST_PASSWORD:
        print("❌ Credentials missing")
        return False
        
    variations = generate_pin_variations(title, focus_kw)
    driver = create_pinterest_driver()
    
    if not login_to_pinterest(driver):
        driver.quit()
        return False
        
    success_count = 0
    article_url = f"{BLOG_SITE}/{permalink}"
    
    try:
        for i, pin in enumerate(variations):
            print(f"\n📌 Processing Pin {i+1}/3")
            path = f"temp_pin_{i}_{permalink}.png"
            create_pin_image(featured_image_path, pin['hook'], path, i)
            full_desc = f"{pin['description']}\n\n{pin['hashtags']}"
            
            if upload_pin_to_pinterest(driver, path, pin['title'], full_desc, article_url):
                success_count += 1
            if os.path.exists(path): os.remove(path)
            if i < len(variations) - 1: time.sleep(10)
                
    finally:
        driver.quit()
    return success_count > 0