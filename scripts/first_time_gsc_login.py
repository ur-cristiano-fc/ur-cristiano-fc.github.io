"""
First-time GSC Login Script - Simple Selenium Version
No SSL issues, works on all platforms
"""

import os
import time
import json
import base64
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class GSCFirstTimeLogin:
    """Handle first-time login with regular Selenium"""
    
    def __init__(self, profile_dir="./gsc_chrome_profile"):
        self.profile_dir = Path(profile_dir)
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome with persistent profile"""
        # Create profile directory if it doesn't exist
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        print("🌐 Opening Chrome browser...")
        
        options = Options()
        options.add_argument(f"--user-data-dir={self.profile_dir.absolute()}")
        
        # Anti-bot detection (basic)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Add realistic user agent
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Hide webdriver flag
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.driver.maximize_window()
        print("✅ Browser ready!")
        
    def perform_manual_login(self):
        """Guide user through manual login with 2FA"""
        print("\n" + "="*60)
        print("🔐 MANUAL LOGIN REQUIRED")
        print("="*60)
        
        print("\n💡 TIP: If Google blocks you with 'This browser is not secure':")
        print("   1. Click 'Try again'")
        print("   2. Or use 'Sign in with a different account'")
        print("   3. Complete the security checks")
        print("\nOpening Google Search Console...\n")
        
        # Navigate to GSC
        self.driver.get("https://search.google.com/search-console")
        
        print("="*60)
        print("📋 INSTRUCTIONS:")
        print("="*60)
        print("1. Login with your Google account")
        print("2. Complete any security checks (2FA, CAPTCHA, etc.)")
        print("3. Make sure you reach the GSC dashboard")
        print("4. You should see your properties listed")
        print("="*60)
        
        input("\n⏸️  Press ENTER after you've successfully logged in and see the GSC dashboard: ")
        
        # Verify we're logged in
        current_url = self.driver.current_url
        
        if "search.google.com/search-console" in current_url:
            print("✅ Login verified! You're on Google Search Console")
            return True
        else:
            print(f"⚠️  Current URL: {current_url}")
            confirm = input("Are you sure you're logged in and on GSC? (y/n): ")
            return confirm.lower() == 'y'
    
    def verify_session(self):
        """Verify the session works"""
        print("\n" + "="*60)
        print("🔍 VERIFYING SESSION PERSISTENCE")
        print("="*60)
        
        # Close and reopen browser
        print("Closing browser...")
        self.driver.quit()
        time.sleep(2)
        
        print("Reopening browser with saved profile...")
        self.setup_driver()
        
        print("Navigating to GSC...")
        self.driver.get("https://search.google.com/search-console")
        time.sleep(5)
        
        current_url = self.driver.current_url
        
        if "search.google.com/search-console" in current_url and "signin" not in current_url.lower():
            print("✅ Session verified! Auto-login works!")
            return True
        else:
            print(f"⚠️  Session verification failed")
            print(f"   Current URL: {current_url}")
            return False
    
    def save_cookies_json(self):
        """Save cookies as JSON"""
        print("\n" + "="*60)
        print("🍪 SAVING COOKIES")
        print("="*60)
        
        try:
            cookies = self.driver.get_cookies()
            
            # Save cookies to JSON
            cookies_file = "gsc_cookies.json"
            with open(cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            # Save as base64
            cookies_json = json.dumps(cookies)
            cookies_base64 = base64.b64encode(cookies_json.encode()).decode()
            
            cookies_base64_file = "gsc_cookies_base64.txt"
            with open(cookies_base64_file, 'w') as f:
                f.write(cookies_base64)
            
            print(f"✅ Cookies saved to: {cookies_file}")
            print(f"✅ Cookies (base64) saved to: {cookies_base64_file}")
            print(f"📊 Size: {len(cookies_base64):,} characters")
            
            if len(cookies_base64) > 64000:
                print(f"⚠️  Cookies too large for GitHub Secrets ({len(cookies_base64):,} > 64,000)")
                return False
            else:
                print(f"✅ Size OK for GitHub Secrets!")
                return True
                
        except Exception as e:
            print(f"❌ Cookie export failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_instructions(self):
        """Generate setup instructions"""
        print("\n" + "="*60)
        print("📚 NEXT STEPS")
        print("="*60)
        
        instructions = """
✅ SESSION SAVED SUCCESSFULLY!

╔════════════════════════════════════════════════════════════╗
║              ADD TO GITHUB SECRETS                         ║
╚════════════════════════════════════════════════════════════╝

1. Open file: gsc_cookies_base64.txt

2. Copy ALL content (Ctrl+A → Ctrl+C or Cmd+A → Cmd+C)

3. Go to GitHub:
   Your Repo → Settings → Secrets and variables → Actions

4. Click "New repository secret"

5. Add:
   Name:  GSC_COOKIES_BASE64
   Value: [paste the copied content]

6. Click "Add secret"


╔════════════════════════════════════════════════════════════╗
║                 REFRESH SESSION (Future)                   ║
╚════════════════════════════════════════════════════════════╝

When automation stops working (after ~60 days):
1. Run this script again
2. Login manually
3. Update the GSC_COOKIES_BASE64 secret with new value


╔════════════════════════════════════════════════════════════╗
║                    YOU'RE DONE!                            ║
╚════════════════════════════════════════════════════════════╝

Your GitHub Actions workflow will now automatically:
✓ Generate blog posts
✓ Submit them to Google Search Console
✓ Handle indexing requests

No manual work needed! 🎉
"""
        print(instructions)
        
        # Save to file
        with open("GITHUB_SETUP_INSTRUCTIONS.txt", 'w') as f:
            f.write(instructions)
        
        print("📄 Instructions saved to: GITHUB_SETUP_INSTRUCTIONS.txt")
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()


def main():
    """Main execution"""
    print("="*60)
    print("🚀 GSC First-Time Login Setup")
    print("="*60)
    print("\nThis script will:")
    print("  1. Open Chrome browser")
    print("  2. Let you login to GSC manually")
    print("  3. Save your authenticated session")
    print("  4. Export cookies for GitHub Actions")
    print("\n" + "="*60)
    
    input("Press ENTER to begin...")
    
    login_manager = GSCFirstTimeLogin()
    
    try:
        # Step 1: Open browser and login
        login_manager.setup_driver()
        
        if not login_manager.perform_manual_login():
            print("\n❌ Login failed or was cancelled")
            return
        
        # Step 2: Save cookies
        print("\n⏳ Saving session data...")
        time.sleep(2)
        
        if not login_manager.save_cookies_json():
            print("\n❌ Failed to save cookies")
            return
        
        # Step 3: Verify session persistence
        if not login_manager.verify_session():
            print("\n⚠️  Session verification failed")
            print("💡 The cookies were saved, but you may need to try again")
            return
        
        # Step 4: Success!
        print("\n" + "="*60)
        print("🎉 SUCCESS!")
        print("="*60)
        
        login_manager.generate_instructions()
        
        print("\n✅ Setup complete!")
        print("📖 Read GITHUB_SETUP_INSTRUCTIONS.txt for next steps")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Closing browser...")
        login_manager.close()


if __name__ == "__main__":
    main()