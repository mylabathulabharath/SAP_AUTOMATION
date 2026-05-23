import os
import sys
import time
from playwright.sync_api import sync_playwright

def run_automation():
    # Retrieve CDP port connection details (defaults to local port 2222)
    cdp_url = os.environ.get("CDP_URL", "http://localhost:2222")
    
    print(f"[INFO] Connecting to Chrome over CDP at: {cdp_url}...")
    
    try:
        with sync_playwright() as p:
            # Connect to existing Chrome debugging session
            browser = p.chromium.connect_over_cdp(cdp_url)
            
            # Retrieve or create active page
            if browser.contexts:
                context = browser.contexts[0]
                page = context.new_page() if not context.pages else context.pages[0]
            else:
                context = browser.new_context()
                page = context.new_page()
            
            print("[INFO] Connected successfully!")
            
            # Step 1: Navigate to the target page (using Google for testing)
            target_url = "https://www.google.com"
            print(f"[INFO] Navigating to: {target_url}")
            page.goto(target_url)
            
            # Step 2: Pause for MFA / Login
            print("\n" + "="*70)
            print("  PAUSE REQUIRED: Please complete your login/MFA in the browser window.")
            print("  When you are fully authenticated and ready to proceed, return here.")
            print("="*70)
            input("Press [ENTER] in this terminal to continue the automation...")
            
            # Step 3: Proceed with the task (testing search)
            print("\n[INFO] Resuming automation...")
            print("[INFO] Waiting for search input element...")
            page.wait_for_selector("[name=q]", timeout=15000)
            
            print("[INFO] Typing 'mangoes'...")
            page.fill("[name=q]", "mangoes")
            
            print("[INFO] Submitting search...")
            page.keyboard.press("Enter")
            
            # Step 4: Let the page load the results
            time.sleep(3)
            print("[SUCCESS] Automation run complete. Results are displayed in the Chrome tab.")
            
            # Note: We do not call page.close() or browser.close() here.
            # Because we connected via CDP, exiting the script simply detaches Playwright,
            # leaving the Chrome window and your tab open on your desktop.

    except Exception as e:
        print(f"\n[ERROR] Automation execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_automation()
