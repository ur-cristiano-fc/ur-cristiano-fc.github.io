"""
Check if your Chrome profile is valid and logged into GSC
Run this before pushing to GitHub to verify everything works
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time


def check_chrome_profile(headless=False):
    """Check if chrome_profile has valid GSC login"""
    
    print("="*60)
    print("🔍 CHECKING CHROME PROFILE")
    print("="*60)
    print(f"Mode: {'Headless' if headless else 'Visible'}")
    print("="*60 + "\n")
    
    options = Options()
    options.add_argument("user-data-dir=./chrome_profile")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        print("Step 1: Opening Google Search Console...")
        driver.get("https://search.google.com/search-console")
        
        print("⏳ Waiting 10 seconds for page to load...")
        time.sleep(10)
        
        # Take screenshot
        driver.save_screenshot("debug_login_check.png")
        print("📸 Screenshot saved: debug_login_check.png")
        
        # Check page content
        page_source = driver.page_source.lower()
        page_title = driver.title.lower()
        current_url = driver.current_url
        
        print(f"\n📊 Page Analysis:")
        print(f"  URL: {current_url}")
        print(f"  Title: {driver.title}")
        
        # Check if logged in
        if "sign in" in page_source or "sign in" in page_title:
            print("\n❌ NOT LOGGED IN")
            print("="*60)
            print("Your Chrome profile doesn't have a valid GSC session.")
            print("\n📋 To fix:")
            print("1. Run: python3 scripts/first_time_gsc_login.py")
            print("2. Log in manually when the browser opens")
            print("3. Make sure you see the GSC dashboard")
            print("4. Then run this check again")
            return False
        
        elif "search console" in page_title or "overview" in page_source:
            print("\n✅ LOGGED IN!")
            print("="*60)
            print("Your Chrome profile has a valid GSC session.")
            
            # Try to find property
            if "ur-cristiano-fc" in page_source or "github.io" in page_source:
                print("✅ Found your property in the page")
            else:
                print("⚠️  Could not find your property, but you are logged in")
            
            print("\n📋 Next steps:")
            print("1. Test the full automation: python3 test_gsc_locally.py")
            print("2. If that works, push to GitHub")
            return True
        
        else:
            print("\n⚠️  UNCLEAR STATUS")
            print("="*60)
            print("Could not determine if you're logged in.")
            print(f"Page title: {driver.title}")
            print("\n📋 Please manually check:")
            print("1. Open the screenshot: debug_login_check.png")
            print("2. Make sure you see the GSC dashboard")
            print("3. If not, run: python3 scripts/first_time_gsc_login.py")
            return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if not headless:
            input("\nPress Enter to close browser...")
        driver.quit()
        print("\n✅ Browser closed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Check Chrome profile GSC login')
    parser.add_argument('--headless', action='store_true', help='Check in headless mode')
    args = parser.parse_args()
    
    success = check_chrome_profile(headless=args.headless)
    
    if success:
        print("\n" + "="*60)
        print("✅ ALL GOOD - Ready for automation!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ ISSUE DETECTED - Please fix before using automation")
        print("="*60)