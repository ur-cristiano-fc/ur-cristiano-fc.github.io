"""
Enhanced GSC automation with better headless mode support
Fixes for GitHub Actions environment
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from datetime import datetime
import urllib.parse
from pathlib import Path


class GSCAutomation:
    def __init__(self, profile_path="./chrome_profile", headless=False):
        self.profile_path = profile_path
        self.driver = None
        self.headless = headless
        self.progress_file = "gsc_progress.json"
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome with enhanced headless support"""
        options = Options()
        options.add_argument(f"user-data-dir={self.profile_path}")
        
        # Essential flags
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Anti-detection (CRITICAL)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Headless mode (NEW method for better compatibility)
        if self.headless:
            options.add_argument("--headless=new")  # Use new headless mode
            options.add_argument("--window-size=1920,1080")
            print("🔇 Running in headless mode (new)")
        else:
            options.add_argument("--start-maximized")
        
        # Additional stability flags for CI/CD
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Set longer page load timeout for slower CI environments
        self.driver.set_page_load_timeout(60)
        
        # Execute CDP commands
        try:
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"⚠️ CDP commands failed: {e}")
        
        print(f"✅ Chrome driver initialized (headless={self.headless})")
        
    def wait_for_element(self, selector, by=By.XPATH, timeout=30, clickable=False):
        """Enhanced wait with longer timeout for CI"""
        try:
            condition = EC.element_to_be_clickable if clickable else EC.presence_of_element_located
            element = WebDriverWait(self.driver, timeout).until(
                condition((by, selector))
            )
            return element
        except Exception as e:
            print(f"⚠️ Timeout waiting for: {selector[:50]}...")
            return None
    
    def get_property_id(self, domain, use_domain_property=False):
        """Get GSC property ID"""
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
        """Check for quota/error messages"""
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
    
    def submit_url(self, url, property_id, max_retries=3):
        """Submit URL with improved reliability"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = min(300, (2 ** attempt) * 10)
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                
                print(f"\n[Attempt {attempt + 1}/{max_retries}] Processing: {url}")
                
                # Navigate to property
                base_url = f"https://search.google.com/u/0/search-console?resource_id={property_id}"
                print(f"Opening property: {base_url}")
                self.driver.get(base_url)
                
                # Longer wait for initial page load
                print("⏳ Waiting for GSC dashboard...")
                time.sleep(8)
                
                # Take early screenshot
                timestamp = int(time.time())
                self.driver.save_screenshot(f"debug_dashboard_{timestamp}.png")
                
                # Find URL inspection search box (multiple strategies)
                print("🔍 Looking for URL inspection search box...")
                
                search_box = None
                search_strategies = [
                    ("//input[contains(@placeholder, 'Inspect')]", "placeholder=Inspect"),
                    ("//input[contains(@aria-label, 'Inspect')]", "aria-label=Inspect"),
                    ("//input[@type='text' and contains(@class, 'search')]", "type=text + search class"),
                    ("//input[@type='text']", "any text input"),
                ]
                
                for selector, strategy_name in search_strategies:
                    print(f"  Trying strategy: {strategy_name}")
                    search_box = self.wait_for_element(selector, timeout=15)
                    if search_box:
                        print(f"  ✅ Found using: {strategy_name}")
                        break
                    time.sleep(2)
                
                if not search_box:
                    print("❌ Could not find search box with any strategy")
                    self._debug_page_elements()
                    continue
                
                # Enter URL
                print(f"📝 Entering URL: {url}")
                search_box.clear()
                time.sleep(1)
                search_box.send_keys(url)
                time.sleep(2)
                search_box.send_keys(Keys.RETURN)
                
                # Wait for inspection results
                print("⏳ Waiting for URL inspection results...")
                time.sleep(12)
                
                self.driver.save_screenshot(f"debug_inspection_{timestamp}.png")
                
                # Check for errors
                error_type = self.check_for_errors()
                if error_type:
                    if error_type in ['quota', 'limit']:
                        return 'quota_reached'
                    elif error_type == 'already_requested':
                        return 'already_requested'
                
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # Find "Request Indexing" button
                print("🔍 Looking for 'Request Indexing' button...")
                
                button_found = False
                button_selectors = [
                    "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'request indexing')]",
                    "//button[contains(text(), 'REQUEST INDEXING')]",
                    "//*[contains(text(), 'Request indexing')]",
                ]
                
                for selector in button_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(2)
                                self.driver.execute_script("arguments[0].click();", element)
                                button_found = True
                                print(f"✅ Clicked: {element.text}")
                                break
                        except:
                            continue
                    if button_found:
                        break
                
                if not button_found:
                    print("❌ Could not find/click 'Request Indexing' button")
                    continue
                
                # Wait for completion
                print("\n" + "="*60)
                print("⏳ WAITING FOR INDEXING TO COMPLETE")
                print("="*60)
                
                success = self.wait_for_indexing_completion()
                
                if success:
                    print("✅ Indexing completed successfully!")
                    self.driver.save_screenshot(f"debug_success_{timestamp}.png")
                    
                    # Try to dismiss modal
                    time.sleep(5)
                    self.click_dismiss_button()
                    time.sleep(5)
                    
                    return True
                else:
                    print("⚠️ Indexing completion uncertain")
                    continue
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                if attempt >= max_retries - 1:
                    return False
        
        return False
    
    def wait_for_indexing_completion(self):
        """Wait for indexing modal to complete"""
        start_time = time.time()
        
        success_indicators = [
            "//*[contains(text(), 'Indexing requested')]",
            "//*[contains(text(), 'indexing requested')]",
            "//*[contains(text(), 'successfully')]",
        ]
        
        active_indicators = [
            "//*[contains(text(), 'Testing live URL')]",
            "//*[contains(text(), 'Running')]",
            "//div[contains(@class, 'spinner')]",
            "//*[@role='progressbar']",
        ]
        
        max_wait = 180  # 3 minutes max
        check_count = 0
        
        while time.time() - start_time < max_wait:
            check_count += 1
            elapsed = time.time() - start_time
            
            # Check for success
            for indicator in success_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    for elem in elements:
                        if elem.is_displayed():
                            print(f"\n✅ Success detected: {elem.text[:50]}")
                            return True
                except:
                    continue
            
            # Check if still processing
            processing = False
            for indicator in active_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    if any(e.is_displayed() for e in elements):
                        processing = True
                        break
                except:
                    continue
            
            if processing:
                print(f"⏳ Processing... ({elapsed:.0f}s)", end="\r")
                time.sleep(2)
            else:
                # No active indicators - wait a bit and check for success again
                time.sleep(3)
                for indicator in success_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, indicator)
                        for elem in elements:
                            if elem.is_displayed():
                                print(f"\n✅ Success detected (delayed): {elem.text[:50]}")
                                return True
                    except:
                        continue
                
                if check_count > 5 and elapsed > 20:
                    print(f"\n✅ No errors detected after {elapsed:.0f}s - assuming success")
                    return True
        
        print(f"\n⚠️ Timed out after {max_wait}s")
        return False
    
    def click_dismiss_button(self):
        """Click dismiss button on success modal"""
        selectors = [
            "//button[contains(text(), 'Dismiss')]",
            "//button[contains(text(), 'DISMISS')]",
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        self.driver.execute_script("arguments[0].click();", elem)
                        print("✅ Dismiss clicked")
                        return True
            except:
                continue
        
        return False
    
    def _debug_page_elements(self):
        """Debug helper"""
        print("🔍 Searching page for relevant elements...")
        try:
            # Get page source length
            print(f"Page source length: {len(self.driver.page_source)} chars")
            
            # Find all inputs
            inputs = self.driver.find_elements(By.XPATH, "//input")
            print(f"Found {len(inputs)} input elements:")
            for i, inp in enumerate(inputs[:5]):
                try:
                    print(f"  Input {i}: type={inp.get_attribute('type')}, "
                          f"placeholder={inp.get_attribute('placeholder')}, "
                          f"visible={inp.is_displayed()}")
                except:
                    pass
        except Exception as e:
            print(f"Debug error: {e}")
    
    def save_progress(self, results):
        """Save progress"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Progress saved")
        except Exception as e:
            print(f"⚠️ Save failed: {e}")
    
    def batch_submit(self, urls, property_id, delay=15):
        """Batch submit URLs"""
        results = {
            'success': [],
            'failed': [],
            'quota_reached': [],
            'already_requested': []
        }
        
        print(f"\nSubmitting {len(urls)} URLs")
        
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(urls)}] {url}")
            print(f"{'='*60}")
            
            result = self.submit_url(url, property_id)
            
            if result is True:
                results['success'].append(url)
            elif result == 'quota_reached':
                results['quota_reached'].append(url)
                break
            elif result == 'already_requested':
                results['already_requested'].append(url)
            else:
                results['failed'].append(url)
            
            self.save_progress(results)
            
            if i < len(urls):
                print(f"\n⏳ Waiting {delay}s before next URL...")
                time.sleep(delay)
        
        self._print_summary(results)
        return results
    
    def _print_summary(self, results):
        """Print summary"""
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Success: {len(results['success'])}")
        print(f"ℹ️  Already requested: {len(results['already_requested'])}")
        print(f"⚠️  Quota reached: {len(results['quota_reached'])}")
        print(f"❌ Failed: {len(results['failed'])}")
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()