import sqlite3
import os

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
DB_PATH = os.path.join(DB_DIR, "database.db")

def get_db_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create Vendors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        address TEXT,
        email TEXT,
        gst_number TEXT,
        phone TEXT,
        payment_terms TEXT
    )
    """)
    
    # 2. Create Purchase Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number TEXT UNIQUE NOT NULL,
        vendor_id TEXT NOT NULL,
        invoice_number TEXT,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        status TEXT NOT NULL, -- Draft, Pending, Approved, Rejected, Hold
        approval_status TEXT NOT NULL, -- Pending, Approved, Rejected
        created_date TEXT NOT NULL,
        FOREIGN KEY (vendor_id) REFERENCES vendors (vendor_id)
    )
    """)
    
    # 3. Create Invoices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        po_number TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        status TEXT NOT NULL, -- Pending, Verified, Approved, Rejected
        created_date TEXT NOT NULL,
        FOREIGN KEY (po_number) REFERENCES purchase_orders (po_number)
    )
    """)
    
    # 4. Create Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number TEXT NOT NULL,
        action TEXT NOT NULL, -- Created, Searched, Verified, Approved, Rejected, Hold
        performed_by TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        details TEXT,
        FOREIGN KEY (po_number) REFERENCES purchase_orders (po_number)
    )
    """)
    
    # 5. Create Automation Runs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS automation_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        po_number TEXT NOT NULL,
        status TEXT NOT NULL, -- Success, Failed, Running
        duration_seconds REAL,
        screenshot_dir TEXT,
        logs TEXT,
        timestamp TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

if __name__ == "__main__":
    init_db()
