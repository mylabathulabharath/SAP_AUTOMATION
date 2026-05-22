import os
import sys
import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker

# Add apps/shared/ to path to import database.py
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database import init_db, get_db_connection

fake = Faker()
Faker.seed(42)
random.seed(42)

def seed_data():
    print("Seeding database...")
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Clear existing data
    cursor.execute("DELETE FROM automation_runs")
    cursor.execute("DELETE FROM audit_logs")
    cursor.execute("DELETE FROM invoices")
    cursor.execute("DELETE FROM purchase_orders")
    cursor.execute("DELETE FROM vendors")
    conn.commit()
    
    # 2. Seed 100 Vendors
    vendors = []
    payment_terms_options = ["Net 30", "Net 45", "Net 60", "Due on Receipt", "2% 10 Net 30"]
    
    for i in range(100):
        vendor_id = f"VEND-{100000 + i}"
        name = fake.company()
        address = f"{fake.street_address()}, {fake.city()}, {fake.state_abbr()} {fake.zipcode()}"
        email = f"info@{name.lower().replace(' ', '').replace(',', '').replace('.', '')}.com"
        gst_number = f"{random.randint(10, 99)}AAAAA{random.randint(1000, 9999)}A{random.randint(1, 9)}Z{random.randint(1, 9)}"
        phone = fake.phone_number()
        payment_terms = random.choice(payment_terms_options)
        
        cursor.execute("""
        INSERT INTO vendors (vendor_id, name, address, email, gst_number, phone, payment_terms)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id, name, address, email, gst_number, phone, payment_terms))
        
        vendors.append({
            "vendor_id": vendor_id,
            "name": name,
            "payment_terms": payment_terms
        })
    
    conn.commit()
    print("Seeded 100 vendors.")
    
    # 3. Seed 1000 Purchase Orders
    po_list = []
    statuses = ["Draft", "Pending", "Approved", "Rejected", "Hold"]
    approval_statuses = {
        "Draft": "Pending",
        "Pending": "Pending",
        "Approved": "Approved",
        "Rejected": "Rejected",
        "Hold": "Pending"
    }
    currencies = ["USD", "EUR", "GBP", "INR", "CAD"]
    
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(1000):
        po_number = f"4500{i:04d}" # 45000000 to 45000999
        vendor = random.choice(vendors)
        vendor_id = vendor["vendor_id"]
        vendor_name = vendor["name"]
        
        status = random.choice(statuses)
        # For seeding, let's make most POs "Pending" or "Draft" so Playwright has pending items to approve/reject
        if random.random() < 0.6:
            status = "Pending"
            
        approval_status = approval_statuses[status]
        amount = round(random.uniform(500, 150000), 2)
        currency = random.choice(currencies)
        
        # Format dates
        po_date = start_date + timedelta(days=random.randint(0, 360))
        created_date = po_date.strftime("%Y-%m-%d")
        
        # Invoice number
        invoice_number = None
        if status in ["Approved", "Rejected", "Hold", "Pending"] and random.random() < 0.8:
            invoice_number = f"INV-{900000 + i}"
            
        cursor.execute("""
        INSERT INTO purchase_orders (po_number, vendor_id, invoice_number, amount, currency, status, approval_status, created_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (po_number, vendor_id, invoice_number, amount, currency, status, approval_status, created_date))
        
        po_list.append({
            "po_number": po_number,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "invoice_number": invoice_number,
            "amount": amount,
            "currency": currency,
            "status": status,
            "created_date": created_date
        })
        
    conn.commit()
    print("Seeded 1000 purchase orders.")
    
    # 4. Seed Invoices for POs with invoice numbers
    seeded_invoices = 0
    for po in po_list:
        if po["invoice_number"]:
            # Create invoice record
            inv_status = "Pending"
            if po["status"] == "Approved":
                inv_status = "Approved"
            elif po["status"] == "Rejected":
                inv_status = "Rejected"
            
            cursor.execute("""
            INSERT INTO invoices (invoice_number, po_number, amount, currency, status, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (po["invoice_number"], po["po_number"], po["amount"], po["currency"], inv_status, po["created_date"]))
            seeded_invoices += 1
            
    conn.commit()
    print(f"Seeded {seeded_invoices} invoices.")
    
    # 5. Seed Audit Logs
    seeded_logs = 0
    for po in po_list:
        # Every PO has a "Created" log
        created_time = datetime.strptime(po["created_date"], "%Y-%m-%d")
        log_time = created_time + timedelta(hours=random.randint(1, 4))
        
        cursor.execute("""
        INSERT INTO audit_logs (po_number, action, performed_by, timestamp, details)
        VALUES (?, ?, ?, ?, ?)
        """, (po["po_number"], "Created", "SYSTEM", log_time.strftime("%Y-%m-%d %H:%M:%S"), "Purchase Order created in SAP ERP"))
        seeded_logs += 1
        
        if po["status"] != "Draft" and po["status"] != "Pending":
            action_time = log_time + timedelta(days=random.randint(1, 5))
            cursor.execute("""
            INSERT INTO audit_logs (po_number, action, performed_by, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
            """, (po["po_number"], po["status"], "admin", action_time.strftime("%Y-%m-%d %H:%M:%S"), f"Status updated to {po['status']} by Admin user"))
            seeded_logs += 1
            
    conn.commit()
    print(f"Seeded {seeded_logs} audit logs.")
    
    # 6. Generate Excel file sample_po_list.xlsx for user download
    # Select 50 POs that are currently "Pending" so the automation can process them.
    pending_pos = [po for po in po_list if po["status"] == "Pending"]
    if len(pending_pos) < 50:
        pending_pos = po_list[:50]
    else:
        pending_pos = random.sample(pending_pos, 50)
        
    excel_rows = []
    # Mix of expected statuses to test automation flows
    status_flow = ["Approved", "Rejected", "Hold"]
    for idx, po in enumerate(pending_pos):
        excel_rows.append({
            "po_number": po["po_number"],
            "vendor_name": po["vendor_name"],
            "expected_status": status_flow[idx % len(status_flow)],
            "invoice_number": po["invoice_number"] if po["invoice_number"] else f"INV-GEN-{random.randint(10000, 99999)}"
        })
        
    df = pd.DataFrame(excel_rows)
    
    # Create the frontend public sample-data directory if it doesn't exist
    frontend_public_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sap-simulator", "frontend", "public", "sample-data"))
    os.makedirs(frontend_public_dir, exist_ok=True)
    
    excel_path = os.path.join(frontend_public_dir, "sample_po_list.xlsx")
    df.to_excel(excel_path, index=False)
    print(f"Generated sample Excel at: {excel_path}")
    
    conn.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_data()
