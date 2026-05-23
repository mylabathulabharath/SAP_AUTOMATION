import os
import sys
import time
import json
import argparse
import traceback
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright

# Add shared directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))
from database import get_db_connection

# Resolve file paths
PLAYWRIGHT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.abspath(os.path.join(PLAYWRIGHT_DIR, ".."))
OUTPUT_DIR = os.path.join(ENGINE_DIR, "outputs")
STATUS_FILE_PATH = os.path.join(OUTPUT_DIR, "status.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def update_status(status, current_po, processed, total, success, failure, start_time):
    status_data = {
        "status": status,
        "current_po": current_po,
        "processed_count": processed,
        "total_count": total,
        "success_count": success,
        "failure_count": failure,
        "start_time": start_time
    }
    with open(STATUS_FILE_PATH, "w") as f:
        json.dump(status_data, f, indent=2)

def run_automation(excel_path):
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO] Starting run at {start_time}")
    
    # 1. Read Excel file
    if not os.path.exists(excel_path):
        print(f"[ERROR] Excel file not found at {excel_path}")
        return False
        
    try:
        df = pd.read_excel(excel_path)
        po_rows = df.to_dict('records')
    except Exception as e:
        print(f"[ERROR] Failed to read Excel file: {str(e)}")
        return False
        
    total_pos = len(po_rows)
    print(f"[INFO] Loaded {total_pos} PO rows from Excel.")
    
    processed_count = 0
    success_count = 0
    failure_count = 0
    
    update_status("running", "Starting Browser...", processed_count, total_pos, success_count, failure_count, start_time)
    
    with sync_playwright() as p:
        cdp_url = os.environ.get("CDP_URL")
        if cdp_url:
            print(f"[INFO] Connecting to remote browser over CDP: {cdp_url}")
            browser = p.chromium.connect_over_cdp(cdp_url)
            if browser.contexts:
                context = browser.contexts[0]
                page = context.new_page() if not context.pages else context.pages[0]
            else:
                context = browser.new_context()
                page = context.new_page()
        else:
            print("[INFO] Launching Chromium browser...")
            browser = p.chromium.launch(headless=False, args=["--no-sandbox", "--disable-setuid-sandbox"])
            context = browser.new_context(viewport={"width": 1280, "height": 850})
            page = context.new_page()
        
        # Base URL of SAP Simulator
        base_url = "http://localhost:3000"
        
        try:
            print("[INFO] Navigating to login page...")
            page.goto(f"{base_url}/login")
            time.sleep(1.5)
            
            # Perform Login
            print("[INFO] Submitting login credentials...")
            page.fill("#login-username", "admin")
            page.fill("#login-password", "admin123")
            page.click("#btn-login")
            
            # Wait for dashboard to load
            page.wait_for_selector("#nav-dashboard", timeout=5000)
            print("[INFO] Login successful. Routed to Dashboard.")
            time.sleep(1)
            
        except Exception as e:
            print(f"[ERROR] Login failed: {str(e)}")
            update_status("failed", "Login Failed", processed_count, total_pos, success_count, failure_count, start_time)
            browser.close()
            return False
            
        # Process each PO
        for idx, row in enumerate(po_rows):
            po_number = str(row["po_number"]).strip()
            vendor_name = str(row.get("vendor_name", "")).strip()
            expected_status = str(row.get("expected_status", "Approved")).strip()
            invoice_number = str(row.get("invoice_number", "")).strip()
            
            print(f"\n[INFO] ----------------------------------------")
            print(f"[INFO] Processing PO {po_number} ({idx+1}/{total_pos})")
            print(f"[INFO] Expected Action: {expected_status}, Invoice: {invoice_number}")
            print(f"[INFO] ----------------------------------------")
            
            processed_count = idx
            update_status("running", po_number, processed_count, total_pos, success_count, failure_count, start_time)
            
            po_output_dir = os.path.join(OUTPUT_DIR, po_number)
            os.makedirs(po_output_dir, exist_ok=True)
            
            po_start_time = time.time()
            success = False
            error_message = None
            
            try:
                # STEP 1: Open dashboard and capture screenshot
                print(f"[INFO] Navigating to Dashboard for PO {po_number}...")
                page.click("#nav-dashboard")
                time.sleep(1.5)
                page.screenshot(path=os.path.join(po_output_dir, "dashboard.png"))
                print("[INFO] Saved dashboard.png")
                
                # STEP 2: Navigate to PO Search page
                print("[INFO] Navigating to Purchase Orders Search page...")
                page.click("#nav-pos")
                time.sleep(1)
                
                # STEP 3: Search PO number
                print(f"[INFO] Searching for PO {po_number}...")
                page.fill("#search-po-input", po_number)
                page.click("#btn-search-po")
                time.sleep(1.5) # Wait for table search filter
                
                # STEP 4: Take search result screenshot
                page.screenshot(path=os.path.join(po_output_dir, "search-results.png"))
                print("[INFO] Saved search-results.png")
                
                # STEP 5: Open PO details page
                details_btn_selector = f"#btn-view-details-{po_number}"
                if not page.is_visible(details_btn_selector):
                    # Check if there is a backup fallback selector or if PO wasn't found
                    row_selector = f"text={po_number}"
                    if not page.is_visible(row_selector):
                        raise Exception(f"PO {po_number} not found in search results.")
                    # If found text, click it or look for the view details button
                    page.click(row_selector)
                    time.sleep(1)
                else:
                    page.click(details_btn_selector)
                    time.sleep(1.5)
                    
                # STEP 6: Interact with details page elements
                print("[INFO] Interacting with PO Detail verification components...")
                # Select a verification radio button
                if page.is_visible("#radio-verify-ok"):
                    page.check("#radio-verify-ok")
                time.sleep(0.3)
                
                # Check verification checkboxes
                if page.is_visible("#check-verify-items"):
                    page.check("#check-verify-items")
                if page.is_visible("#check-verify-prices"):
                    page.check("#check-verify-prices")
                time.sleep(0.3)
                
                # Enter verification remarks
                if page.is_visible("#textarea-remarks"):
                    page.fill("#textarea-remarks", f"Automated Playwright verification run. expected_status: {expected_status}, invoice: {invoice_number}")
                time.sleep(0.3)
                
                # Take PO details screenshot
                page.screenshot(path=os.path.join(po_output_dir, "po-details.png"))
                print("[INFO] Saved po-details.png")
                
                # STEP 7: Open Invoice Tab and take screenshot
                print("[INFO] Clicking Invoice tab...")
                if page.is_visible("#tab-invoice"):
                    page.click("#tab-invoice")
                    time.sleep(0.8)
                    page.screenshot(path=os.path.join(po_output_dir, "invoice-tab.png"))
                    print("[INFO] Saved invoice-tab.png")
                else:
                    print("[WARNING] Invoice tab not found.")
                    
                # STEP 8: Go back to Details/Approval and execute action
                if page.is_visible("#tab-details"):
                    page.click("#tab-details")
                    time.sleep(0.5)
                    
                # Execute Action based on expected status
                print(f"[INFO] Performing action '{expected_status}' on PO {po_number}...")
                action_btn_id = f"#btn-{expected_status.lower()}"
                if page.is_visible(action_btn_id):
                    # Scroll button into view
                    page.locator(action_btn_id).scroll_into_view_if_needed()
                    time.sleep(0.3)
                    page.click(action_btn_id)
                    time.sleep(1.5) # Wait for action submission and toast
                    
                    # Capture approval section screenshot (or screen showing final result)
                    page.screenshot(path=os.path.join(po_output_dir, "approval-section.png"))
                    print("[INFO] Saved approval-section.png")
                    success = True
                else:
                    raise Exception(f"Action button {action_btn_id} not visible on page.")
                    
            except Exception as e:
                error_message = str(e)
                print(f"[ERROR] Failed to process PO {po_number}: {error_message}")
                traceback.print_exc()
                
                # Capture failure screenshot
                try:
                    page.screenshot(path=os.path.join(po_output_dir, "failure.png"))
                    print("[INFO] Saved failure.png")
                except Exception:
                    pass
                    
            po_end_time = time.time()
            po_duration = round(po_end_time - po_start_time, 2)
            
            # Log results to database and update success/failure counts
            status_str = "Success" if success else "Failed"
            if success:
                success_count += 1
            else:
                failure_count += 1
                
            # Write PO metadata
            metadata = {
                "po_number": po_number,
                "vendor_name": vendor_name,
                "expected_status": expected_status,
                "invoice_number": invoice_number,
                "status": status_str,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": po_duration,
                "error": error_message
            }
            with open(os.path.join(po_output_dir, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)
                
            # Update SQLite table: automation_runs
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                run_id = f"RUN-{start_time.replace(' ', 'T')}"
                cursor.execute("""
                    INSERT INTO automation_runs (run_id, po_number, status, duration_seconds, screenshot_dir, logs, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id, 
                    po_number, 
                    status_str, 
                    po_duration, 
                    po_output_dir, 
                    f"Processed PO {po_number}. Expected: {expected_status}. Result: {status_str}." + (f" Error: {error_message}" if error_message else ""), 
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                conn.commit()
            except Exception as dbe:
                print(f"[ERROR] Failed to insert run log into DB: {str(dbe)}")
            finally:
                conn.close()
                
            print(f"[INFO] PO {po_number} processed in {po_duration}s. Status: {status_str}")
            
        print("[INFO] Closing browser...")
        browser.close()
        
    final_processed_count = total_pos
    update_status("completed", "All Done", final_processed_count, total_pos, success_count, failure_count, start_time)
    print(f"\n[INFO] Automation run completed. Processed: {final_processed_count}, Success: {success_count}, Failed: {failure_count}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Playwright SAP Simulator Automation")
    parser.add_argument("excel_path", type=str, help="Path to the Excel sheet containing PO numbers")
    args = parser.parse_args()
    
    run_automation(args.excel_path)
