import os
import sys
import time
from playwright.sync_api import sync_playwright

def main():
    # If run in docker, CDP_URL will be set to http://host.docker.internal:2222
    # If run on host, fallback to http://localhost:2222
    cdp_url = os.environ.get("CDP_URL", "http://localhost:2222")
    
    print(f"[INFO] Connecting to Chrome over CDP at: {cdp_url}...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url)
            
            # Select or create a page
            if browser.contexts:
                context = browser.contexts[0]
                page = context.new_page() if not context.pages else context.pages[0]
            else:
                context = browser.new_context()
                page = context.new_page()
            
            print("[INFO] Connection successful! Navigating to Google...")
            page.goto("https://www.google.com")
            
            print("[INFO] Waiting for search input...")
            # Google search selector is usually [name=q] or textarea[name=q]
            page.wait_for_selector("[name=q]", timeout=5000)
            
            print("[INFO] Typing 'mangoes' and submitting search...")
            page.fill("[name=q]", "mangoes")
            page.keyboard.press("Enter")
            
            # Wait for search results
            time.sleep(3)
            print("[INFO] Search completed successfully!")
            
            # Close the tab we opened/used
            page.close()
            
    except Exception as e:
        print(f"[ERROR] Failed to run test: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
