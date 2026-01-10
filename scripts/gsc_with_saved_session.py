"""
GSC Automation using Saved Session (Cookies)
Uses pre-authenticated session from first_time_gsc_login.py
"""

import os
import json
import time
import base64
import urllib.parse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class GSCAutomationWithSession:
    """GSC Automation using saved cookies/session"""
    
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        self.cookies_loaded = False
        
    def setup_driver(self):
        """Setup Chrome driver"""
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            print("🔇 Running in headless mode")
        
        # Additional stability options
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        if not self.headless:
            self.driver.maximize_window()
    
    def load_cookies_from_base64(self, cookies_base64):
        """
        Load cookies from base64 encoded string (from GitHub Secret)
        
        Args:
            cookies_base64: Base64 encoded JSON cookies
        """
        try:
            print("🍪 Loading cookies from GitHub Secret...")
            
            # Decode base64
            cookies_json = base64.b64decode(cookies_base64).decode('utf-8')
            cookies = json.loads(cookies_json)
            
            # Must navigate to domain first before adding cookies
            print("📍 Navigating to Google domain...")
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Add all cookies
            print(f"🍪 Adding {len(cookies)} cookies...")
            for cookie in cookies:
                try:
                    # Remove problematic fields
                    if 'expiry' in cookie:
                        cookie['expiry'] = int(cookie['expiry'])
                    
                    # Selenium doesn't accept 'sameSite' as None
                    if 'sameSite' in cookie and cookie['sameSite'] is None:
                        del cookie['sameSite']
                    
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    # Some cookies may fail, that's OK
                    continue
            
            print("✅ Cookies loaded successfully")
            self.cookies_loaded = True
            return True
            
        except Exception as e:
            print(f"❌ Failed to load cookies: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_authentication(self):
        """Verify that we're authenticated to GSC"""
        print("🔍 Verifying authentication...")
        
        try:
            self.driver.get("https://search.google.com/search-console")
            time.sleep(5)
            
            current_url = self.driver.current_url
            
            # Check if we're on the login page
            if "signin" in current_url.lower() or "accounts.google.com" in current_url:
                print("❌ Not authenticated - redirected to login page")
                return False
            
            # Check if we're on GSC
            if "search.google.com/search-console" in current_url:
                print("✅ Authentication verified - on GSC dashboard")
                return True
            
            print(f"⚠️  Unexpected URL: {current_url}")
            return False
            
        except Exception as e:
            print(f"❌ Authentication verification failed: {e}")
            return False
    
    def wait_for_element(self, selector, by=By.XPATH, timeout=15, clickable=False):
        """Smart wait with configurable condition"""
        try:
            condition = EC.element_to_be_clickable if clickable else EC.presence_of_element_located
            element = WebDriverWait(self.driver, timeout).until(
                condition((by, selector))
            )
            return element
        except Exception as e:
            print(f"⚠️ Wait timeout for selector: {selector[:50]}...")
            return None
    
    def get_property_id(self, domain, use_domain_property=False):
        """Get the property ID for GSC"""
        if use_domain_property:
            clean_domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
            return urllib.parse.quote(f"sc-domain:{clean_domain}", safe='')
        else:
            if not domain.startswith("http"):
                domain = f"https://{domain}"
            if not domain.endswith("/"):
                domain = f"{domain}/"
            return urllib.parse.quote(domain, safe='')
    
    def check_for_errors(self):
        """Check for quota limits or other errors"""
        error_indicators = [
            ("//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'quota')]", "quota"),
            ("//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'limit')]", "limit"),
            ("//*[contains(text(), 'already requested')]", "already_requested"),
            ("//*[contains(text(), 'Already requested')]", "already_requested"),
        ]
        
        for selector, error_type in error_indicators:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and any(elem.is_displayed() for elem in elements):
                    return error_type
            except:
                continue
        
        return None
    
    def click_dismiss_button(self):
        """Click the Dismiss button on the success modal"""
        print("🔍 Looking for Dismiss button...")
        
        dismiss_selectors = [
            "//button[contains(text(), 'Dismiss')]",
            "//button[contains(text(), 'DISMISS')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dismiss')]",
            "//*[@role='button' and contains(text(), 'Dismiss')]",
            "//span[contains(text(), 'Dismiss')]//ancestor::button",
        ]
        
        for selector in dismiss_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", element)
                            print("✅ Dismiss button clicked successfully")
                            return True
                    except:
                        continue
            except:
                continue
        
        return False
    
    def wait_for_indexing_completion(self):
        """Wait for the indexing process to complete"""
        print("⏳ Waiting for indexing modal to appear...")
        start_time = time.time()
        
        # Wait for modal to appear
        modal_appeared = False
        for _ in range(50):
            try:
                modal_selectors = [
                    "//div[contains(@role, 'dialog')]",
                    "//div[contains(@class, 'modal')]",
                    "//*[contains(text(), 'Testing live URL')]",
                    "//*[contains(text(), 'Running')]",
                ]
                
                for selector in modal_selectors:
                    try:
                        element = self.driver.find_element(By.XPATH, selector)
                        if element.is_displayed():
                            print(f"✅ Indexing modal detected!")
                            modal_appeared = True
                            break
                    except:
                        continue
                
                if modal_appeared:
                    break
                    
                time.sleep(0.2)
            except:
                time.sleep(0.2)
        
        if not modal_appeared:
            print("⚠️ Modal didn't appear, but continuing to monitor...")
        
        # Monitor for completion
        print("⏳ Monitoring indexing process...")
        time.sleep(3)
        
        success_indicators = [
            "//*[contains(text(), 'Indexing requested')]",
            "//*[contains(text(), 'indexing requested')]",
            "//*[contains(text(), 'Request received')]",
            "//*[contains(text(), 'successfully')]",
        ]
        
        active_process_indicators = [
            "//*[contains(text(), 'Testing live URL')]",
            "//*[contains(text(), 'Running tests')]",
            "//*[contains(text(), 'Checking')]",
            "//div[contains(@class, 'spinner')]",
            "//*[@role='progressbar']",
        ]
        
        last_status = ""
        check_count = 0
        
        while True:
            try:
                check_count += 1
                elapsed = time.time() - start_time
                
                # Check for success
                for indicator in success_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, indicator)
                        for element in elements:
                            if element.is_displayed():
                                success_text = element.text[:50]
                                print(f"\n✅ SUCCESS: '{success_text}'")
                                print(f"✅ Completed in {elapsed:.1f}s")
                                return True
                    except:
                        continue
                
                # Check if still processing
                process_active = False
                for indicator in active_process_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, indicator)
                        for element in elements:
                            if element.is_displayed():
                                process_active = True
                                break
                        if process_active:
                            break
                    except:
                        continue
                
                if process_active:
                    print(f"⏳ Processing... ({elapsed:.0f}s)", end="\r")
                    time.sleep(1)
                else:
                    # No activity detected
                    time.sleep(2)
                    
                    # Final check for success
                    for indicator in success_indicators:
                        try:
                            elements = self.driver.find_elements(By.XPATH, indicator)
                            for element in elements:
                                if element.is_displayed():
                                    print(f"\n✅ Complete in {elapsed:.1f}s")
                                    return True
                        except:
                            continue
                    
                    # Check if modal closed
                    try:
                        modals = self.driver.find_elements(By.XPATH, "//div[contains(@role, 'dialog')]")
                        visible_modals = [m for m in modals if m.is_displayed()]
                        
                        if not visible_modals and elapsed > 15:
                            print(f"\n✅ Modal closed - complete ({elapsed:.1f}s)")
                            return True
                    except:
                        pass
                    
                    if check_count > 10 and elapsed > 20:
                        print(f"\n✅ Assuming complete ({elapsed:.1f}s)")
                        return True
                    
                    time.sleep(2)
                
            except Exception as e:
                print(f"\n⚠️ Error: {e}")
                time.sleep(2)
    
    def submit_url(self, url, property_id, max_retries=3):
        """Submit a single URL for indexing"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = min(300, (2 ** attempt) * 10)
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                
                print(f"\n[Attempt {attempt + 1}/{max_retries}] Processing: {url}")
                
                # Navigate to property
                base_url = f"https://search.google.com/u/0/search-console?resource_id={property_id}"
                print(f"Opening property...")
                self.driver.get(base_url)
                time.sleep(5)
                
                # Find URL inspection search box
                search_selectors = [
                    "//input[contains(@placeholder, 'Inspect any URL')]",
                    "//input[contains(@aria-label, 'Inspect')]",
                    "//input[@type='text']",
                ]
                
                search_box = None
                for selector in search_selectors:
                    search_box = self.wait_for_element(selector, timeout=10)
                    if search_box:
                        print("✅ Found URL inspection search box")
                        break
                
                if not search_box:
                    print("❌ Could not find search box")
                    continue
                
                # Enter URL
                print(f"Entering URL...")
                search_box.clear()
                search_box.send_keys(url)
                time.sleep(1)
                search_box.send_keys(Keys.RETURN)
                time.sleep(10)
                
                # Screenshot for debugging
                timestamp = int(time.time())
                self.driver.save_screenshot(f"debug_inspection_{timestamp}.png")
                
                # Wait for results
                self.wait_for_element(
                    "//*[contains(text(), 'URL is not on Google') or contains(text(), 'URL is on Google')]",
                    timeout=15
                )
                time.sleep(3)
                
                # Check for errors
                error_type = self.check_for_errors()
                if error_type:
                    print(f"⚠️ Error: {error_type}")
                    if error_type in ['quota', 'limit']:
                        return 'quota_reached'
                    elif error_type == 'already_requested':
                        return 'already_requested'
                
                # Scroll and find Request Indexing button
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                print("Looking for 'Request Indexing' button...")
                
                selectors = [
                    "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'request indexing')]",
                    "//*[contains(text(), 'Request indexing')]",
                    "//*[contains(text(), 'REQUEST INDEXING')]",
                ]
                
                element_found = False
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(1)
                                self.driver.execute_script("arguments[0].click();", element)
                                element_found = True
                                print("✅ Clicked 'Request Indexing'")
                                break
                        if element_found:
                            break
                    except:
                        continue
                
                if not element_found:
                    print("❌ Could not find 'Request Indexing' button")
                    continue
                
                # Wait for completion
                print("\n" + "="*60)
                print("⏳ WAITING FOR INDEXING TO COMPLETE")
                print("="*60)
                
                self.wait_for_indexing_completion()
                
                print("✅ SUCCESS: Indexing request completed!")
                
                # Screenshot
                self.driver.save_screenshot(f"debug_success_{timestamp}.png")
                
                # Dismiss modal
                time.sleep(5)
                self.click_dismiss_button()
                time.sleep(5)
                
                self.driver.save_screenshot(f"debug_final_{timestamp}.png")
                
                return True
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                if attempt >= max_retries - 1:
                    return False
        
        return False
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()


def get_latest_post_url(posts_dir="_posts", domain="https://ur-cristiano-fc.github.io"):
    """Get the URL of the most recently created post"""
    try:
        posts_path = Path(posts_dir)
        if not posts_path.exists():
            print(f"❌ Posts directory not found: {posts_dir}")
            return None
        
        posts = list(posts_path.glob("*.md"))
        if not posts:
            print(f"⚠️ No posts found")
            return None
        
        latest_post = max(posts, key=lambda p: p.stat().st_mtime)
        filename = latest_post.stem
        parts = filename.split('-', 3)
        
        if len(parts) >= 4:
            permalink = parts[3]
        else:
            permalink = filename
        
        url = f"{domain.rstrip('/')}/{permalink}"
        print(f"📄 Latest post: {latest_post.name}")
        print(f"🔗 URL: {url}")
        
        return url
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Main execution"""
    print("=" * 60)
    print("🚀 GSC Auto-Indexing with Saved Session")
    print("=" * 60)
    
    # Get configuration from environment
    DOMAIN = os.environ.get("SITE_DOMAIN", "https://ur-cristiano-fc.github.io")
    GSC_COOKIES_BASE64 = os.environ.get("GSC_COOKIES_BASE64")
    USE_DOMAIN_PROPERTY = os.environ.get("USE_DOMAIN_PROPERTY", "false").lower() == "true"
    
    # Validate
    if not GSC_COOKIES_BASE64:
        print("❌ GSC_COOKIES_BASE64 not found in environment!")
        print("   Run first_time_gsc_login.py and add the secret to GitHub")
        return
    
    print(f"🌐 Domain: {DOMAIN}")
    
    # Get latest post
    latest_url = get_latest_post_url(domain=DOMAIN)
    if not latest_url:
        print("⚠️ No post to submit")
        return
    
    # Initialize bot
    bot = None
    
    try:
        bot = GSCAutomationWithSession(headless=True)
        bot.setup_driver()
        
        # Load saved session
        if not bot.load_cookies_from_base64(GSC_COOKIES_BASE64):
            print("❌ Failed to load session")
            return
        
        # Verify authentication
        if not bot.verify_authentication():
            print("❌ Authentication failed - session may have expired")
            print("💡 Run first_time_gsc_login.py again to refresh session")
            return
        
        # Get property ID
        property_id = bot.get_property_id(DOMAIN, use_domain_property=USE_DOMAIN_PROPERTY)
        print(f"🔑 Property ID: {property_id[:30]}...")
        
        # Submit URL
        print(f"\n{'=' * 60}")
        print("📤 Submitting to Google Search Console")
        print("=" * 60)
        
        result = bot.submit_url(latest_url, property_id)
        
        if result is True:
            print(f"\n{'=' * 60}")
            print("✅ SUCCESS!")
            print("=" * 60)
            print(f"📄 URL submitted: {latest_url}")
        elif result == 'quota_reached':
            print(f"\n⚠️ QUOTA REACHED - will retry tomorrow")
        elif result == 'already_requested':
            print(f"\nℹ️ ALREADY REQUESTED - skipping")
        else:
            print(f"\n❌ FAILED - check logs")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if bot:
            bot.close()
            print("\n👋 Browser closed")


if __name__ == "__main__":
    main()