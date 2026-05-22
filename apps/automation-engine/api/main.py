import os
import sys
import shutil
import json
import subprocess
import zipfile
from typing import Optional
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add apps/shared to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))
from database import get_db_connection

app = FastAPI(title="Automation Engine API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
LOG_FILE_PATH = os.path.join(OUTPUT_DIR, "run_logs.txt")
STATUS_FILE_PATH = os.path.join(OUTPUT_DIR, "status.json")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mount outputs as static files so frontend can fetch screenshots directly
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# Helper to load status
def load_status():
    if os.path.exists(STATUS_FILE_PATH):
        try:
            with open(STATUS_FILE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "status": "idle",
        "current_po": "",
        "processed_count": 0,
        "total_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "start_time": ""
    }

# Helper to save status
def save_status(status_dict):
    with open(STATUS_FILE_PATH, "w") as f:
        json.dump(status_dict, f, indent=2)

# Background task runner
def run_playwright_subprocess(excel_path: str):
    # Set status to running
    status = {
        "status": "running",
        "current_po": "Initializing...",
        "processed_count": 0,
        "total_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "start_time": subprocess.check_output(["date"]).decode().strip()
    }
    save_status(status)
    
    # Empty existing logs
    with open(LOG_FILE_PATH, "w") as f:
        f.write("[INFO] Starting automation engine...\n")
        
    runner_path = os.path.join(BASE_DIR, "playwright", "automation_runner.py")
    python_exec = sys.executable # Path to the venv python interpreter
    
    # Run the playwright runner as a subprocess
    process = subprocess.Popen(
        [python_exec, runner_path, excel_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1 # Line buffered
    )
    
    # Stream stdout/stderr to the log file in real-time
    with open(LOG_FILE_PATH, "a") as f:
        for line in process.stdout:
            f.write(line)
            f.flush()
            
    process.wait()
    
    # Final check
    final_status = load_status()
    if final_status["status"] == "running":
        final_status["status"] = "completed" if process.returncode == 0 else "failed"
        save_status(final_status)
        
    with open(LOG_FILE_PATH, "a") as f:
        if process.returncode == 0:
            f.write(f"\n[SUCCESS] Automation run finished successfully (Code: {process.returncode})\n")
        else:
            f.write(f"\n[ERROR] Automation run failed with exit code: {process.returncode}\n")

@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported.")
        
    file_path = os.path.join(UPLOAD_DIR, "po_list.xlsx")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Read total count from Excel to initialize status
    import pandas as pd
    try:
        df = pd.read_excel(file_path)
        total_count = len(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel file: {str(e)}")
        
    # Initialize status
    status = {
        "status": "idle",
        "current_po": "",
        "processed_count": 0,
        "total_count": total_count,
        "success_count": 0,
        "failure_count": 0,
        "start_time": ""
    }
    save_status(status)
    
    # Clear outputs directory (except logs and status) to avoid mixing old/new screenshots
    for item in os.listdir(OUTPUT_DIR):
        item_path = os.path.join(OUTPUT_DIR, item)
        if item_path not in [LOG_FILE_PATH, STATUS_FILE_PATH] and os.path.isdir(item_path):
            shutil.rmtree(item_path)
            
    # Clear log file
    with open(LOG_FILE_PATH, "w") as f:
        f.write("[INFO] Excel file uploaded and parsed successfully. Ready to start automation.\n")
        
    return {
        "filename": file.filename,
        "rows_count": total_count,
        "status": "ready"
    }

@app.post("/api/start-automation")
def start_automation(background_tasks: BackgroundTasks):
    status = load_status()
    if status["status"] == "running":
        return {"status": "error", "message": "Automation is already running."}
        
    excel_path = os.path.join(UPLOAD_DIR, "po_list.xlsx")
    if not os.path.exists(excel_path):
        # Fallback to sample data Excel if user hasn't uploaded anything
        sample_path = os.path.abspath(os.path.join(BASE_DIR, "..", "sap-simulator", "frontend", "public", "sample-data", "sample_po_list.xlsx"))
        if os.path.exists(sample_path):
            shutil.copy(sample_path, excel_path)
            # update total_count
            import pandas as pd
            df = pd.read_excel(excel_path)
            status["total_count"] = len(df)
            save_status(status)
        else:
            raise HTTPException(status_code=400, detail="No Excel file uploaded. Please upload a file first.")
            
    background_tasks.add_task(run_playwright_subprocess, excel_path)
    return {"status": "success", "message": "Automation triggered successfully."}

@app.get("/api/automation-status")
def get_automation_status():
    return load_status()

@app.get("/api/logs")
def get_logs():
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "r") as f:
            # Return last 200 lines to prevent page bloat
            lines = f.readlines()
            return {"logs": "".join(lines[-200:])}
    return {"logs": "[INFO] No logs available."}

@app.get("/api/reports")
def get_reports():
    reports = []
    if os.path.exists(OUTPUT_DIR):
        for item in sorted(os.listdir(OUTPUT_DIR)):
            item_path = os.path.join(OUTPUT_DIR, item)
            if os.path.isdir(item_path):
                metadata_path = os.path.join(item_path, "metadata.json")
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, "r") as f:
                            reports.append(json.load(f))
                    except Exception:
                        pass
    return {"reports": reports}

@app.get("/api/download-output")
def download_output():
    zip_path = os.path.join(BASE_DIR, "automation_outputs.zip")
    
    # Create a zip of all directories in OUTPUT_DIR
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                # Exclude the temporary txt or status json if wanted, or include them. Include everything.
                arcname = os.path.relpath(file_path, OUTPUT_DIR)
                zipf.write(file_path, arcname)
                
    return FileResponse(
        path=zip_path,
        filename="automation_outputs.zip",
        media_type="application/zip"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
