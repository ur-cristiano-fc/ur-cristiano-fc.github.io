"""First-time GSC login helper script

Run this ONCE on your local machine to save GSC login credentials.
Then commit and push the chrome_profile folder to GitHub.

Usage:
    python scripts/first_time_gsc_login.py
"""

import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def setup_undetected_chrome(profile_path="./chrome_profile"):
    """
    Setup Chrome with options to avoid detection as automated browser
    """
    options = Options()
    
    # Use existing profile or create new one
    options.add_argument(f"user-data-dir={profile_path}")
    
    # IMPORTANT: These flags help avoid "This browser may not be secure" error
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Additional flags for better compatibility
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    
    # Set a real user agent
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Execute CDP commands to further hide automation
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def main():
    print("="*60)
    print("🔐 Google Search Console First-Time Login")
    print("="*60)
    print()
    print("This script will:")
    print("1. Open Chrome browser (with anti-detection)")
    print("2. Navigate to Google Search Console")
    print("3. Wait for you to log in manually")
    print("4. Save your login session to ./chrome_profile")
    print()
    print("⚠️  IMPORTANT:")
    print("- Use a Google account that has access to your GSC property")
    print("- Complete 2FA/CAPTCHA if prompted")
    print("- Chrome will look like a normal browser (not automated)")
    print("- After login, you'll need to commit and push the chrome_profile folder")
    print("- Make sure your repo is PRIVATE (chrome_profile contains session cookies)")
    print()
    
    response = input("Ready to proceed? (y/n): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return
    
    print("\n🚀 Starting browser with anti-detection...")
    
    driver = None
    try:
        # Setup Chrome with anti-detection
        driver = setup_undetected_chrome(profile_path="./chrome_profile")
        
        print("✅ Chrome started successfully")
        print("📱 Opening Google Search Console...")
        
        driver.get("https://search.google.com/search-console")
        
        print("\n" + "="*60)
        print("PLEASE LOG IN MANUALLY")
        print("="*60)
        print()
        print("👉 The Chrome window should now be open")
        print("👉 Log in to your Google account")
        print("👉 Complete any 2FA/CAPTCHA challenges")
        print("👉 Wait for GSC dashboard to load")
        print()
        
        input("Press Enter after logging in and seeing the GSC dashboard: ")
        
        print("\n✅ Login saved successfully!")
        print()
        print("="*60)
        print("📋 Next Steps:")
        print("="*60)
        print()
        print("1. Verify the chrome_profile folder exists:")
        print("   ls -la chrome_profile/")
        print()
        print("2. Make sure your repo is PRIVATE:")
        print("   Go to GitHub → Settings → Danger Zone")
        print("   Check it says 'Private repository'")
        print()
        print("3. Commit and push to GitHub:")
        print("   git add chrome_profile/")
        print("   git commit -m 'Add GSC authenticated session'")
        print("   git push")
        print()
        print("4. Test locally (optional):")
        print("   python scripts/generate_posts.py")
        print()
        print("5. Your GitHub Actions workflow will now use this profile!")
        print("   The automation will work even when your MacBook is off.")
        print()
        
        # Close browser
        if driver:
            driver.quit()
        
        print("="*60)
        print("✅ Setup Complete!")
        print("="*60)
        print()
        print("You only need to do this once.")
        print("After pushing chrome_profile/, everything runs automatically!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print()
        print("Troubleshooting tips:")
        print("- Make sure Chrome is installed")
        print("- Try running with administrator/sudo privileges")
        print("- Check your internet connection")
        print("- If Google still blocks login, try using a different Google account")
        print("- Make sure you're not using a VPN or proxy")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()