# Save this as gsc_automation_enhanced.py

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
import csv
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
        """Setup Chrome driver with optional headless mode and anti-detection"""
        options = Options()
        options.add_argument(f"user-data-dir={self.profile_path}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Anti-detection measures - CRITICAL for avoiding "This browser may not be secure"
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set realistic user agent
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            print("🔇 Running in headless mode")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Execute CDP commands to further hide automation
        try:
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"⚠️ Could not execute CDP commands: {e}")
        
        if not self.headless:
            self.driver.maximize_window()
        
    def first_time_login(self):
        """Guide user through first-time login"""
        print("Opening Google Search Console...")
        self.driver.get("https://search.google.com/search-console")
        
        print("\n" + "="*60)
        print("PLEASE LOG IN MANUALLY")
        print("="*60)
        input("Press Enter after logging in: ")
        print("✅ Login saved!")
        
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
        """
        Get the property ID for GSC
        
        Args:
            domain: Your domain (e.g., "langchain-tutorials.github.io" or "https://langchain-tutorials.github.io/")
            use_domain_property: If True, use domain property (sc-domain:), else use URL prefix
        """
        if use_domain_property:
            # Domain property format: sc-domain:example.com
            clean_domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
            return urllib.parse.quote(f"sc-domain:{clean_domain}", safe='')
        else:
            # URL prefix property format: https://example.com/
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
        """
        Click the Dismiss button on the success modal
        
        Returns:
            True if button was found and clicked, False otherwise
        """
        print("🔍 Looking for Dismiss button...")
        
        # Multiple selectors for the Dismiss button
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
                            # Scroll to element
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            
                            # Click using JavaScript
                            self.driver.execute_script("arguments[0].click();", element)
                            print("✅ Dismiss button clicked successfully")
                            return True
                    except:
                        continue
            except:
                continue
        
        return False
    
    def wait_for_indexing_completion(self):
        """
        Wait indefinitely for the indexing process to complete after clicking Request Indexing
        
        GSC shows a modal dialog during indexing. We need to:
        1. Wait for modal to appear
        2. Monitor the modal content for progress
        3. Wait until modal shows completion or disappears
        
        Returns:
            True if indexing completed successfully
        """
        print("⏳ Waiting for indexing modal to appear...")
        start_time = time.time()
        
        # Wait for the indexing modal/dialog to appear first (up to 10 seconds)
        modal_appeared = False
        for _ in range(50):  # 50 * 0.2s = 10 seconds
            try:
                # Look for modal/dialog indicators
                modal_selectors = [
                    "//div[contains(@role, 'dialog')]",
                    "//div[contains(@class, 'modal')]",
                    "//div[contains(@class, 'dialog')]",
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
            print("⚠️ Modal didn't appear, but continuing to monitor for completion...")
        
        # Now wait for the process to complete
        print("⏳ Monitoring indexing process (waiting until completion)...")
        time.sleep(3)  # Give it a moment to start processing
        
        # Success indicators that show the process is complete
        success_indicators = [
            "//*[contains(text(), 'Indexing requested')]",
            "//*[contains(text(), 'indexing requested')]",
            "//*[contains(text(), 'Request received')]",
            "//*[contains(text(), 'request received')]",
            "//*[contains(text(), 'successfully')]",
            "//*[contains(text(), 'Successfully')]",
        ]
        
        # Active process indicators (while these exist, process is running)
        active_process_indicators = [
            "//*[contains(text(), 'Testing live URL')]",
            "//*[contains(text(), 'Running tests')]",
            "//*[contains(text(), 'Checking')]",
            "//*[contains(text(), 'Please wait')]",
            "//div[contains(@class, 'spinner')]",
            "//div[contains(@class, 'loading')]",
            "//div[contains(@class, 'progress')]",
            "//*[@role='progressbar']",
        ]
        
        last_status = ""
        check_count = 0
        
        while True:  # Infinite loop - will only exit when completion is confirmed
            try:
                check_count += 1
                elapsed = time.time() - start_time
                
                # FIRST: Check if success message appeared
                success_found = False
                for indicator in success_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, indicator)
                        for element in elements:
                            if element.is_displayed():
                                success_text = element.text[:50]
                                print(f"\n✅ SUCCESS MESSAGE DETECTED: '{success_text}'")
                                print(f"✅ Indexing process completed in {elapsed:.1f}s")
                                return True
                    except:
                        continue
                
                # SECOND: Check if process is still active
                process_active = False
                current_status = ""
                
                for indicator in active_process_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, indicator)
                        for element in elements:
                            if element.is_displayed():
                                process_active = True
                                if element.text:
                                    current_status = element.text[:40]
                                break
                        if process_active:
                            break
                    except:
                        continue
                
                if process_active:
                    # Process is still running
                    if current_status and current_status != last_status:
                        print(f"\n⏳ Status: {current_status} ({elapsed:.0f}s)")
                        last_status = current_status
                    else:
                        print(f"⏳ Indexing in progress... ({elapsed:.0f}s elapsed)", end="\r")
                    time.sleep(1)
                else:
                    # No active indicators detected
                    print(f"\n🔍 No active process indicators... checking for completion ({elapsed:.0f}s)")
                    
                    # Wait a bit and check again for success message
                    time.sleep(2)
                    
                    for indicator in success_indicators:
                        try:
                            elements = self.driver.find_elements(By.XPATH, indicator)
                            for element in elements:
                                if element.is_displayed():
                                    success_text = element.text[:50]
                                    print(f"✅ SUCCESS MESSAGE FOUND: '{success_text}'")
                                    print(f"✅ Indexing process completed in {elapsed:.1f}s")
                                    return True
                        except:
                            continue
                    
                    # Check if modal closed (which also indicates completion)
                    try:
                        modals = self.driver.find_elements(By.XPATH, "//div[contains(@role, 'dialog')]")
                        visible_modals = [m for m in modals if m.is_displayed()]
                        
                        if not visible_modals and elapsed > 15:
                            print(f"✅ Modal closed - indexing appears complete ({elapsed:.1f}s)")
                            return True
                    except:
                        pass
                    
                    # If we've checked multiple times and found nothing active
                    if check_count > 10 and elapsed > 20:
                        print(f"✅ No activity detected after {elapsed:.1f}s - assuming complete")
                        return True
                    
                    # Keep waiting
                    print("⏳ Continuing to monitor...")
                    time.sleep(2)
                
            except Exception as e:
                print(f"\n⚠️ Error during monitoring: {e}")
                time.sleep(2)
                # Don't exit - keep trying
    
    def submit_url(self, url, property_id, max_retries=3):
        """Submit a single URL for indexing via URL Inspection"""
        for attempt in range(max_retries):
            try:
                # Exponential backoff for retries
                if attempt > 0:
                    wait_time = min(300, (2 ** attempt) * 10)
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                
                print(f"\n[Attempt {attempt + 1}/{max_retries}] Processing: {url}")
                
                # Step 1: Go to the property's URL inspection page
                base_url = f"https://search.google.com/u/0/search-console?resource_id={property_id}"
                print(f"Opening property: {base_url}")
                self.driver.get(base_url)
                
                print("⏳ Waiting for property page to load...")
                time.sleep(5)
                
                # Step 2: Navigate to URL inspection
                print("Navigating to URL inspection...")
                
                # Try to find the search box to inspect URL
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
                    print("❌ Could not find URL inspection search box")
                    continue
                
                # Step 3: Enter the URL to inspect
                print(f"Entering URL: {url}")
                search_box.clear()
                search_box.send_keys(url)
                time.sleep(1)
                search_box.send_keys(Keys.RETURN)
                
                print("⏳ Waiting for URL inspection to load...")
                time.sleep(10)
                
                # Take a screenshot for debugging
                timestamp = int(time.time())
                screenshot_path = f"debug_inspection_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                print(f"📸 Screenshot saved: {screenshot_path}")
                
                # Step 4: Wait for inspection results
                print("⏳ Waiting for inspection results...")
                
                # Wait for the page to show results
                result_element = self.wait_for_element(
                    "//*[contains(text(), 'URL is not on Google') or contains(text(), 'URL is on Google')]",
                    timeout=15
                )
                
                if result_element:
                    print("✅ Inspection results loaded")
                else:
                    print("⚠️ Could not confirm inspection loaded, continuing anyway...")
                
                time.sleep(3)
                
                # Check for errors before proceeding
                error_type = self.check_for_errors()
                if error_type:
                    print(f"⚠️ Error detected: {error_type}")
                    if error_type in ['quota', 'limit']:
                        return 'quota_reached'
                    elif error_type == 'already_requested':
                        print("ℹ️ URL already has pending indexing request")
                        return 'already_requested'
                
                # Scroll down to ensure element is visible
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Step 5: Find and click "REQUEST INDEXING" text
                print("Looking for 'Request Indexing' button...")
                
                element_found = False
                
                # Case-insensitive search for "request indexing"
                selectors = [
                    "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'request indexing')]",
                    "//*[contains(text(), 'Request indexing')]",
                    "//*[contains(text(), 'REQUEST INDEXING')]",
                    "//*[contains(text(), 'Request Indexing')]",
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        
                        for element in elements:
                            try:
                                # Check if element is visible and clickable
                                if element.is_displayed() and element.is_enabled():
                                    # Scroll to element
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                    time.sleep(1)
                                    
                                    print(f"✅ Found clickable element with text: '{element.text}'")
                                    
                                    # Click using JavaScript (most reliable)
                                    self.driver.execute_script("arguments[0].click();", element)
                                    element_found = True
                                    print("✅ Clicked 'Request Indexing' button")
                                    break
                            except Exception as e:
                                continue
                        
                        if element_found:
                            break
                            
                    except Exception as e:
                        continue
                
                if not element_found:
                    print("❌ Could not find clickable 'Request Indexing' element")
                    self._debug_page_elements()
                    continue
                
                # Step 6: WAIT FOR INDEXING PROCESS TO COMPLETE (NO TIMEOUT)
                print("\n" + "="*60)
                print("⏳ WAITING FOR INDEXING PROCESS TO COMPLETE")
                print("(Will wait as long as needed until process finishes)")
                print("="*60)
                
                indexing_success = self.wait_for_indexing_completion()
                
                print("✅ SUCCESS: Indexing request confirmed and completed!")
                
                # Take screenshot of success message
                success_screenshot = f"debug_success_{timestamp}.png"
                self.driver.save_screenshot(success_screenshot)
                print(f"📸 Success screenshot saved: {success_screenshot}")
                
                # Step 7: Wait 5 seconds, then click Dismiss button
                print("\n⏳ Waiting 5 seconds before dismissing...")
                time.sleep(5)
                
                dismiss_clicked = self.click_dismiss_button()
                
                if dismiss_clicked:
                    print("✅ Dismiss button clicked")
                    # Wait another 5 seconds after dismissing
                    print("⏳ Waiting 5 seconds after dismiss...")
                    time.sleep(5)
                else:
                    print("⚠️ Could not find Dismiss button (may have auto-closed)")
                    time.sleep(2)
                
                # Take final screenshot
                final_screenshot = f"debug_final_{timestamp}.png"
                self.driver.save_screenshot(final_screenshot)
                print(f"📸 Final screenshot saved: {final_screenshot}")
                
                return True
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                if attempt >= max_retries - 1:
                    return False
        
        return False
    
    def _debug_page_elements(self):
        """Debug helper to find relevant elements on page"""
        print("Searching page for any text containing 'request' or 'indexing'...")
        try:
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            print(f"Checking {len(all_elements)} elements:")
            count = 0
            for elem in all_elements:
                try:
                    text = elem.text.lower()
                    if ('request' in text or 'indexing' in text) and len(text) < 50:
                        tag = elem.tag_name
                        print(f"  <{tag}>: '{elem.text}' (visible: {elem.is_displayed()})")
                        count += 1
                        if count >= 10:
                            break
                except:
                    pass
        except Exception as debug_err:
            print(f"Debug error: {debug_err}")
    
    def save_progress(self, results):
        """Save progress to JSON file"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Progress saved to {self.progress_file}")
        except Exception as e:
            print(f"⚠️ Could not save progress: {e}")
    
    def load_progress(self):
        """Load progress from JSON file"""
        try:
            if Path(self.progress_file).exists():
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                print(f"📂 Loaded previous progress from {data.get('timestamp', 'unknown time')}")
                return data.get('results', {'success': [], 'failed': [], 'skipped': []})
        except Exception as e:
            print(f"⚠️ Could not load progress: {e}")
        
        return {'success': [], 'failed': [], 'skipped': [], 'quota_reached': [], 'already_requested': []}
    
    def load_urls_from_csv(self, filename):
        """Load URLs from CSV file (first column)"""
        urls = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header if exists
                for row in reader:
                    if row and row[0].strip():
                        urls.append(row[0].strip())
            print(f"📂 Loaded {len(urls)} URLs from {filename}")
            return urls
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return []
    
    def save_results_to_csv(self, results, filename='gsc_results.csv'):
        """Save results to CSV file"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['URL', 'Status'])
                
                for url in results.get('success', []):
                    writer.writerow([url, 'Success'])
                for url in results.get('failed', []):
                    writer.writerow([url, 'Failed'])
                for url in results.get('skipped', []):
                    writer.writerow([url, 'Skipped'])
                for url in results.get('quota_reached', []):
                    writer.writerow([url, 'Quota Reached'])
                for url in results.get('already_requested', []):
                    writer.writerow([url, 'Already Requested'])
            
            print(f"💾 Results saved to {filename}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
    
    def batch_submit(self, urls, property_id, delay=15, resume=False):
        """
        Batch submit URLs with progress tracking
        
        Args:
            urls: List of URLs to submit
            property_id: GSC property ID
            delay: Seconds to wait between submissions
            resume: If True, skip previously processed URLs
        """
        results = self.load_progress() if resume else {
            'success': [], 
            'failed': [], 
            'skipped': [],
            'quota_reached': [],
            'already_requested': []
        }
        
        # Filter out already processed URLs if resuming
        if resume:
            processed = set(
                results.get('success', []) + 
                results.get('failed', []) + 
                results.get('skipped', []) +
                results.get('quota_reached', []) +
                results.get('already_requested', [])
            )
            urls = [url for url in urls if url not in processed]
            print(f"📋 Resuming: {len(urls)} URLs remaining")
        
        print(f"\nStarting batch submission of {len(urls)} URLs")
        print(f"Property ID: {property_id}\n")
        
        quota_reached = False
        
        for i, url in enumerate(urls, 1):
            if quota_reached:
                print(f"⚠️ Quota reached, skipping remaining URLs")
                results['skipped'].extend(urls[i-1:])
                break
            
            print(f"\n{'='*60}")
            print(f"[{i}/{len(urls)}] Processing URL...")
            print(f"{'='*60}")
            
            result = self.submit_url(url, property_id)
            
            if result is True:
                results['success'].append(url)
            elif result == 'quota_reached':
                results['quota_reached'].append(url)
                quota_reached = True
            elif result == 'already_requested':
                results['already_requested'].append(url)
            else:
                results['failed'].append(url)
            
            # Save progress after each URL
            self.save_progress(results)
            
            if i < len(urls) and not quota_reached:
                print(f"\n⏳ Waiting {delay} seconds before next...")
                time.sleep(delay)
        
        self._print_summary(results)
        return results
    
    def _print_summary(self, results):
        """Print batch submission summary"""
        print(f"\n{'='*60}")
        print("BATCH COMPLETE")
        print(f"{'='*60}")
        print(f"✅ Successful: {len(results.get('success', []))}")
        print(f"ℹ️  Already Requested: {len(results.get('already_requested', []))}")
        print(f"⚠️  Quota Reached: {len(results.get('quota_reached', []))}")
        print(f"⏭️  Skipped: {len(results.get('skipped', []))}")
        print(f"❌ Failed: {len(results.get('failed', []))}")
        
        if results.get('failed'):
            print("\n❌ Failed URLs:")
            for url in results['failed']:
                print(f"  - {url}")
        
        if results.get('quota_reached'):
            print("\n⚠️  Quota Reached URLs:")
            for url in results['quota_reached']:
                print(f"  - {url}")
        
        print(f"{'='*60}\n")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    # Configuration (from your GSC screenshot: https://ur-cristiano-fc.github.io/)
    YOUR_DOMAIN = "https://ur-cristiano-fc.github.io/"
    USE_DOMAIN_PROPERTY = False
    
    # Option 1: URLs in code
    URLS_TO_SUBMIT = [
        "https://ur-cristiano-fc.github.io/example-post-url/",
    ]
    
    # Option 2: Load from CSV (uncomment to use)
    # CSV should have URLs in first column
    # URLS_TO_SUBMIT = None  # Will load from CSV
    CSV_FILE = "urls.csv"
    
    # Initialize bot (set headless=True to run without GUI)
    bot = GSCAutomation(headless=False)
    
    try:
        # First time setup (uncomment for initial login)
        # bot.first_time_login()
        
        # Load URLs from CSV if not defined
        if URLS_TO_SUBMIT is None:
            URLS_TO_SUBMIT = bot.load_urls_from_csv(CSV_FILE)
        
        if not URLS_TO_SUBMIT:
            print("❌ No URLs to submit!")
        else:
            # Get property ID
            property_id = bot.get_property_id(YOUR_DOMAIN, use_domain_property=USE_DOMAIN_PROPERTY)
            print(f"Using property ID: {property_id}")
            
            # Batch submit (set resume=True to skip already processed URLs)
            results = bot.batch_submit(
                URLS_TO_SUBMIT, 
                property_id, 
                delay=15,
                resume=False  # Change to True to resume interrupted batch
            )
            
            # Save results to CSV
            bot.save_results_to_csv(results)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
    finally:
        bot.close()
        print("👋 Browser closed")