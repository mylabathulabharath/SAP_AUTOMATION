import os
import sys
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add apps/shared to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))
from database import get_db_connection

app = FastAPI(title="SAP PO Simulator API")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this. For local demo, allow all.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class ActionRequest(BaseModel):
    action: str # Approve, Reject, Hold, Verify
    remarks: Optional[str] = ""
    performed_by: Optional[str] = "admin"

@app.post("/api/auth/login")
def login(payload: LoginRequest):
    if payload.username == "admin" and payload.password == "admin123":
        return {"status": "success", "token": "mock-sap-jwt-token", "username": "admin"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

@app.get("/api/dashboard/stats")
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Total POs
        cursor.execute("SELECT COUNT(*) FROM purchase_orders")
        total_pos = cursor.fetchone()[0]
        
        # Pending POs
        cursor.execute("SELECT COUNT(*) FROM purchase_orders WHERE status = 'Pending'")
        pending_pos = cursor.fetchone()[0]
        
        # Approved POs
        cursor.execute("SELECT COUNT(*) FROM purchase_orders WHERE status = 'Approved'")
        approved_pos = cursor.fetchone()[0]
        
        # Invoices Count
        cursor.execute("SELECT COUNT(*) FROM invoices")
        invoice_count = cursor.fetchone()[0]
        
        # Automation Status
        cursor.execute("SELECT COUNT(*) FROM automation_runs")
        total_runs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM automation_runs WHERE status = 'Success'")
        success_runs = cursor.fetchone()[0]
        
        return {
            "total_pos": total_pos,
            "pending_pos": pending_pos,
            "approved_pos": approved_pos,
            "invoice_count": invoice_count,
            "automation_runs": total_runs,
            "automation_success_rate": round((success_runs / total_runs * 100), 1) if total_runs > 0 else 0.0
        }
    finally:
        conn.close()

@app.get("/api/dashboard/charts")
def get_charts():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. PO Status Distribution
        cursor.execute("SELECT status, COUNT(*) as count FROM purchase_orders GROUP BY status")
        status_dist = [{"name": row["status"], "value": row["count"]} for row in cursor.fetchall()]
        
        # 2. Monthly Invoices (mocked group by month from created_date)
        cursor.execute("""
            SELECT strftime('%Y-%m', created_date) as month, COUNT(*) as count, SUM(amount) as total_amount 
            FROM invoices 
            GROUP BY month 
            ORDER BY month DESC 
            LIMIT 6
        """)
        monthly_invoices = []
        for row in reversed(cursor.fetchall()):
            month_str = row["month"]
            try:
                date_obj = datetime.strptime(month_str, "%Y-%m")
                month_name = date_obj.strftime("%b")
            except:
                month_name = month_str
            monthly_invoices.append({
                "month": month_name,
                "count": row["count"],
                "amount": round(row["total_amount"] or 0, 2)
            })
            
        # 3. Vendor Analysis (Top 5 vendors by amount)
        cursor.execute("""
            SELECT v.name, COUNT(p.id) as po_count, SUM(p.amount) as total_amount 
            FROM purchase_orders p
            JOIN vendors v ON p.vendor_id = v.vendor_id
            GROUP BY v.vendor_id
            ORDER BY total_amount DESC
            LIMIT 5
        """)
        vendor_analysis = [{
            "vendor": row["name"][:15] + "..." if len(row["name"]) > 15 else row["name"],
            "count": row["po_count"],
            "amount": round(row["total_amount"] or 0, 2)
        } for row in cursor.fetchall()]
        
        return {
            "status_distribution": status_dist,
            "monthly_invoices": monthly_invoices,
            "vendor_analysis": vendor_analysis
        }
    finally:
        conn.close()

@app.get("/api/vendors")
def get_vendors():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM vendors ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

@app.get("/api/pos")
def list_pos(
    po_number: Optional[str] = Query(None),
    vendor_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT p.*, v.name as vendor_name 
            FROM purchase_orders p 
            JOIN vendors v ON p.vendor_id = v.vendor_id
            WHERE 1=1
        """
        params = []
        
        if po_number:
            query += " AND p.po_number LIKE ?"
            params.append(f"%{po_number}%")
        if vendor_id:
            query += " AND p.vendor_id = ?"
            params.append(vendor_id)
        if status:
            query += " AND p.status = ?"
            params.append(status)
        if approval_status:
            query += " AND p.approval_status = ?"
            params.append(approval_status)
            
        query += " ORDER BY p.po_number DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        pos = []
        for r in rows:
            pos.append({
                "po_number": r["po_number"],
                "vendor_id": r["vendor_id"],
                "vendor_name": r["vendor_name"],
                "invoice_number": r["invoice_number"],
                "amount": r["amount"],
                "currency": r["currency"],
                "status": r["status"],
                "approval_status": r["approval_status"],
                "created_date": r["created_date"]
            })
            
        # Get count for pagination
        count_query = "SELECT COUNT(*) FROM purchase_orders WHERE 1=1"
        count_params = []
        if po_number:
            count_query += " AND po_number LIKE ?"
            count_params.append(f"%{po_number}%")
        if vendor_id:
            count_query += " AND vendor_id = ?"
            count_params.append(vendor_id)
        if status:
            count_query += " AND status = ?"
            count_params.append(status)
        if approval_status:
            count_query += " AND approval_status = ?"
            count_params.append(approval_status)
            
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        return {"data": pos, "total": total_count, "limit": limit, "offset": offset}
    finally:
        conn.close()

@app.get("/api/pos/{po_number}")
def get_po_detail(po_number: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get PO Header
        cursor.execute("""
            SELECT p.*, v.name as vendor_name, v.address as vendor_address, 
                   v.email as vendor_email, v.gst_number as vendor_gst, 
                   v.phone as vendor_phone, v.payment_terms as vendor_terms
            FROM purchase_orders p 
            JOIN vendors v ON p.vendor_id = v.vendor_id
            WHERE p.po_number = ?
        """, (po_number,))
        po_row = cursor.fetchone()
        
        if not po_row:
            raise HTTPException(status_code=404, detail="Purchase Order not found")
            
        # Get Invoice Tab details
        invoice = None
        if po_row["invoice_number"]:
            cursor.execute("SELECT * FROM invoices WHERE invoice_number = ?", (po_row["invoice_number"],))
            inv_row = cursor.fetchone()
            if inv_row:
                invoice = {
                    "invoice_number": inv_row["invoice_number"],
                    "amount": inv_row["amount"],
                    "currency": inv_row["currency"],
                    "status": inv_row["status"],
                    "created_date": inv_row["created_date"]
                }
                
        # Get Audit Logs
        cursor.execute("SELECT * FROM audit_logs WHERE po_number = ? ORDER BY timestamp DESC", (po_number,))
        audit_logs = [{
            "action": row["action"],
            "performed_by": row["performed_by"],
            "timestamp": row["timestamp"],
            "details": row["details"]
        } for row in cursor.fetchall()]
        
        # Generate Material line items dynamically so sum matches PO amount exactly
        # 1-3 items
        po_amount = po_row["amount"]
        currency = po_row["currency"]
        
        items = []
        if po_amount > 50000:
            # 3 items
            item1_amount = round(po_amount * 0.5, 2)
            item2_amount = round(po_amount * 0.3, 2)
            item3_amount = round(po_amount - item1_amount - item2_amount, 2)
            
            items = [
                {"item_code": "MAT-001", "description": "Enterprise Server Rack Installation", "quantity": 1, "price": item1_amount, "tax": 18.0, "total": item1_amount},
                {"item_code": "MAT-042", "description": "High Performance Switchboards", "quantity": 15, "price": round(item2_amount / 15, 2), "tax": 18.0, "total": item2_amount},
                {"item_code": "MAT-089", "description": "Fiber Optic Cabling Bundle", "quantity": 100, "price": round(item3_amount / 100, 2), "tax": 18.0, "total": item3_amount}
            ]
        elif po_amount > 10000:
            # 2 items
            item1_amount = round(po_amount * 0.7, 2)
            item2_amount = round(po_amount - item1_amount, 2)
            items = [
                {"item_code": "MAT-203", "description": "Office Laptops (Intel i7)", "quantity": 5, "price": round(item1_amount / 5, 2), "tax": 12.0, "total": item1_amount},
                {"item_code": "MAT-309", "description": "External Monitors 27\"", "quantity": 10, "price": round(item2_amount / 10, 2), "tax": 12.0, "total": item2_amount}
            ]
        else:
            # 1 item
            items = [
                {"item_code": "MAT-901", "description": "Office Stationery Supplies Box", "quantity": 1, "price": po_amount, "tax": 5.0, "total": po_amount}
            ]
            
        # Attachments
        attachments = [
            {"filename": f"PO_{po_number}_signed.pdf", "size": "142 KB", "type": "PDF"},
        ]
        if po_row["invoice_number"]:
            attachments.append({"filename": f"Invoice_{po_row['invoice_number']}.pdf", "size": "210 KB", "type": "PDF"})
            
        # Payment details
        payment_details = {
            "bank_name": "Deutsche Bank AG",
            "account_number": "**** **** **** 8829",
            "payment_terms": po_row["vendor_terms"],
            "currency": currency,
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d") if po_row["created_date"] else None
        }

        # Response structure
        return {
            "header": {
                "po_number": po_row["po_number"],
                "vendor_id": po_row["vendor_id"],
                "vendor_name": po_row["vendor_name"],
                "invoice_number": po_row["invoice_number"],
                "amount": po_row["amount"],
                "currency": po_row["currency"],
                "status": po_row["status"],
                "approval_status": po_row["approval_status"],
                "created_date": po_row["created_date"]
            },
            "vendor": {
                "name": po_row["vendor_name"],
                "address": po_row["vendor_address"],
                "email": po_row["vendor_email"],
                "gst_number": po_row["vendor_gst"],
                "phone": po_row["vendor_phone"],
                "payment_terms": po_row["vendor_terms"]
            },
            "items": items,
            "invoice": invoice,
            "attachments": attachments,
            "audit_logs": audit_logs,
            "payment_details": payment_details
        }
    finally:
        conn.close()

@app.post("/api/pos/{po_number}/action")
def update_po_status(po_number: str, payload: ActionRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if PO exists
        cursor.execute("SELECT * FROM purchase_orders WHERE po_number = ?", (po_number,))
        po = cursor.fetchone()
        if not po:
            raise HTTPException(status_code=404, detail="Purchase Order not found")
            
        # Determine status mapped
        action = payload.action # Approve, Reject, Hold, Verify
        new_status = po["status"]
        new_approval = po["approval_status"]
        
        if action == "Approve":
            new_status = "Approved"
            new_approval = "Approved"
        elif action == "Reject":
            new_status = "Rejected"
            new_approval = "Rejected"
        elif action == "Hold":
            new_status = "Hold"
            new_approval = "Pending"
        elif action == "Verify":
            # If verify, we can mark the invoice as Verified, and set PO status to Pending
            new_status = "Pending"
            new_approval = "Pending"
            
        # Update Purchase Order
        cursor.execute("""
            UPDATE purchase_orders 
            SET status = ?, approval_status = ? 
            WHERE po_number = ?
        """, (new_status, new_approval, po_number))
        
        # Update Invoice status if applicable
        if po["invoice_number"]:
            inv_status = "Pending"
            if action == "Approve":
                inv_status = "Approved"
            elif action == "Reject":
                inv_status = "Rejected"
            elif action == "Verify":
                inv_status = "Verified"
                
            cursor.execute("""
                UPDATE invoices 
                SET status = ? 
                WHERE invoice_number = ?
            """, (inv_status, po["invoice_number"]))
            
        # Add Audit Log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        details = f"Action: {action}. Remarks: {payload.remarks}" if payload.remarks else f"Action: {action}."
        cursor.execute("""
            INSERT INTO audit_logs (po_number, action, performed_by, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (po_number, action, payload.performed_by, timestamp, details))
        
        conn.commit()
        return {"status": "success", "message": f"PO {po_number} successfully updated via action {action}"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
