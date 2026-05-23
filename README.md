# Playwright RPA Automation Runner (Host Chrome Connection via CDP)

A clean, standalone Playwright automation runner designed to control an active Chrome browser session on your Mac host via the Chrome DevTools Protocol (CDP). 

This setup allows you to run automation scripts on real-world portals behind Multi-Factor Authentication (MFA) or Single Sign-On (SSO) by pausing execution for manual login before proceeding.

---

## How It Works

1. **Launches Chrome on Host Mac:** You start a Chrome instance with remote debugging enabled.
2. **Connects via CDP:** The Playwright Python script connects directly to this existing Chrome session.
3. **Pauses for MFA:** The script navigates to the target page, then pauses and prompts you in the terminal to log in.
4. **Resumes Automation:** Once you press `ENTER` in the terminal, the script continues with its tasks.
5. **Leaves Session Open:** Because it attaches to an external Chrome instance, exiting the script does not close the browser tab.

---

## Local Setup

### 1. Initialize Virtual Environment
Ensure you have Playwright installed:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install playwright
playwright install chromium
```

### 2. Launch Chrome in Debugging Mode
Run this command in a new terminal window on your Mac to launch Chrome with remote debugging on port `2222`:
```bash
open -na "Google Chrome" --args --remote-debugging-port=2222 --user-data-dir="$HOME/chrome_debug_profile" --no-first-run --no-default-browser-check
```

### 3. Run the Automation Script
With Chrome running, run the runner script:
```bash
source .venv/bin/activate
python automation_runner.py
```

---

## Testing Verification
During the test execution:
1. Chrome will open and navigate to Google.
2. The terminal will print a pause message asking you to complete login/MFA.
3. Return to the terminal and press `ENTER`.
4. Playwright will search for **"mangoes"** in Chrome and display the results without closing the tab.
