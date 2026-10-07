import os
import secrets
import shutil
from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .database import get_db, init_db, hash_password, verify_password

# Initialize app and paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Initialize Database
init_db()

app = FastAPI(title="Customer Software Hub & Licensing Server")

# Enable CORS for API clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# In-memory simple token session storage for seamless speed
ACTIVE_SESSIONS = {}

# Dependency to get current user from Bearer Token or Cookie
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif "session_token" in request.cookies:
        token = request.cookies.get("session_token")

    if not token or token not in ACTIVE_SESSIONS:
        return None
    return ACTIVE_SESSIONS[token]

def require_admin(user = Depends(get_current_user)):
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

def require_auth(user = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

# Helper to generate readable license key
def generate_key_string(prefix="LIC"):
    p1 = secrets.token_hex(2).upper()
    p2 = secrets.token_hex(2).upper()
    p3 = secrets.token_hex(2).upper()
    return f"{prefix}-{p1}-{p2}-{p3}"

# ==================== WEB PAGES ====================

@app.get("/", response_class=HTMLResponse)
async def index_page():
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Customer Software Server Hub</h1>"

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    admin_file = os.path.join(TEMPLATES_DIR, "admin.html")
    if os.path.exists(admin_file):
        with open(admin_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Admin Panel</h1>"

@app.get("/portal", response_class=HTMLResponse)
async def client_portal_page():
    portal_file = os.path.join(TEMPLATES_DIR, "client.html")
    if os.path.exists(portal_file):
        with open(portal_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Client Portal</h1>"

# ==================== AUTHENTICATION API ====================

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
async def api_login(data: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (data.username,))
    user = cursor.fetchone()
    conn.close()

    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = secrets.token_hex(32)
    user_info = {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "full_name": user["full_name"],
        "company_name": user["company_name"]
    }
    ACTIVE_SESSIONS[token] = user_info

    response = JSONResponse(content={
        "status": "success",
        "token": token,
        "user": user_info
    })
    response.set_cookie(key="session_token", value=token, httponly=True, max_age=86400*7)
    return response

@app.post("/api/auth/logout")
async def api_logout(request: Request):
    token = request.cookies.get("session_token")
    if token and token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]
    response = JSONResponse(content={"status": "logged_out"})
    response.delete_cookie("session_token")
    return response

@app.get("/api/auth/me")
async def api_me(user = Depends(require_auth)):
    return user

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@app.put("/api/auth/change-password")
async def api_change_password(data: ChangePasswordRequest, user = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
    row = cursor.fetchone()
    if not row or not verify_password(data.old_password, row["password_hash"]):
        conn.close()
        raise HTTPException(status_code=400, detail="Purana password ghalat hai!")

    new_hash = hash_password(data.new_password)
    cursor.execute("UPDATE users SET password_hash = ?, plain_password = ? WHERE id = ?", (new_hash, data.new_password, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Admin password kamyabi se tabdeel hogaya!"}

# ==================== ADMIN MANAGEMENT API ====================

@app.get("/api/admin/stats")
async def admin_stats(admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'client'")
    total_clients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM softwares")
    total_softwares = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM licenses WHERE status = 'ACTIVE'")
    active_licenses = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM access_logs WHERE date(created_at) = date('now', 'localtime')")
    today_checks = cursor.fetchone()[0]

    conn.close()
    return {
        "total_clients": total_clients,
        "total_softwares": total_softwares,
        "active_licenses": active_licenses,
        "today_checks": today_checks
    }

# --- Client CRUD ---
class CreateClientRequest(BaseModel):
    username: str
    password: str
    full_name: str
    company_name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""

@app.get("/api/admin/clients")
async def get_clients(admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.plain_password, u.full_name, u.company_name, u.phone, u.email, u.created_at,
               COUNT(l.id) as total_licenses
        FROM users u
        LEFT JOIN licenses l ON u.id = l.user_id
        WHERE u.role = 'client'
        GROUP BY u.id
        ORDER BY u.id DESC
    """)
    clients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return clients

@app.post("/api/admin/clients")
async def create_client(data: CreateClientRequest, admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, plain_password, role, full_name, company_name, phone, email)
            VALUES (?, ?, ?, 'client', ?, ?, ?, ?)
        """, (data.username, hash_password(data.password), data.password, data.full_name, data.company_name, data.phone, data.email))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Username may already exist: {str(e)}")
    conn.close()
    return {"status": "success", "message": "Client created successfully"}

@app.delete("/api/admin/clients/{client_id}")
async def delete_client(client_id: int, admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ? AND role = 'client'", (client_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

class ResetClientPasswordRequest(BaseModel):
    new_password: str

@app.put("/api/admin/clients/{client_id}/password")
async def admin_reset_client_password(client_id: int, data: ResetClientPasswordRequest, admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = ? AND role = 'client'", (client_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Client nahi mila!")

    new_hash = hash_password(data.new_password)
    cursor.execute("UPDATE users SET password_hash = ?, plain_password = ? WHERE id = ?", (new_hash, data.new_password, client_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Client '{row['username']}' ka password update hogaya!"}

# --- Software CRUD ---
@app.get("/api/admin/softwares")
async def get_softwares(admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, COUNT(l.id) as assigned_count
        FROM softwares s
        LEFT JOIN licenses l ON s.id = l.software_id
        GROUP BY s.id
        ORDER BY s.id DESC
    """)
    softwares = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return softwares

@app.post("/api/admin/softwares")
async def create_software(
    app_code: str = Form(...),
    title: str = Form(...),
    version: str = Form("1.0.0"),
    description: str = Form(""),
    download_url: Optional[str] = Form(""),
    file: Optional[UploadFile] = File(None),
    admin = Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor()

    is_local = 0
    saved_filename = ""
    file_size_str = ""

    if file and file.filename:
        is_local = 1
        safe_name = f"{app_code}_{file.filename}"
        dest_path = os.path.join(UPLOADS_DIR, safe_name)
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_filename = file.filename
        size_bytes = os.path.getsize(dest_path)
        file_size_str = f"{size_bytes / (1024*1024):.2f} MB"
        download_url = f"/download/file/{safe_name}"

    try:
        cursor.execute("""
            INSERT INTO softwares (app_code, title, version, description, download_url, is_local_file, file_name, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (app_code, title, version, description, download_url, is_local, saved_filename, file_size_str))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Error creating software: {str(e)}")
    conn.close()
    return {"status": "success", "message": "Software registered successfully"}

@app.delete("/api/admin/softwares/{soft_id}")
async def delete_software(soft_id: int, admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM softwares WHERE id = ?", (soft_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

# --- License CRUD ---
class CreateLicenseRequest(BaseModel):
    user_id: int
    software_id: int
    expiry_date: str = "LIFETIME" # 'YYYY-MM-DD' or 'LIFETIME'
    hardware_lock_enabled: int = 1
    notes: Optional[str] = ""

@app.get("/api/admin/licenses")
async def get_licenses(admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.*, u.full_name as client_name, u.company_name, u.username as client_username,
               s.title as software_title, s.app_code
        FROM licenses l
        JOIN users u ON l.user_id = u.id
        JOIN softwares s ON l.software_id = s.id
        ORDER BY l.id DESC
    """)
    licenses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return licenses

@app.post("/api/admin/licenses")
async def create_license(data: CreateLicenseRequest, admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch software app_code for nice prefix
    cursor.execute("SELECT app_code FROM softwares WHERE id = ?", (data.software_id,))
    soft = cursor.fetchone()
    prefix = soft["app_code"][:4].upper() if soft else "LIC"
    new_key = generate_key_string(prefix)

    cursor.execute("""
        INSERT INTO licenses (license_key, user_id, software_id, status, expiry_date, hardware_lock_enabled, notes)
        VALUES (?, ?, ?, 'ACTIVE', ?, ?, ?)
    """, (new_key, data.user_id, data.software_id, data.expiry_date, data.hardware_lock_enabled, data.notes))
    conn.commit()
    conn.close()
    return {"status": "success", "license_key": new_key}

class UpdateLicenseStatus(BaseModel):
    status: Optional[str] = None # ACTIVE, SUSPENDED, EXPIRED
    reset_machine: Optional[bool] = False
    expiry_date: Optional[str] = None

@app.put("/api/admin/licenses/{license_id}")
async def update_license(license_id: int, data: UpdateLicenseStatus, admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    if data.reset_machine:
        cursor.execute("UPDATE licenses SET machine_id = NULL WHERE id = ?", (license_id,))
    if data.status:
        cursor.execute("UPDATE licenses SET status = ? WHERE id = ?", (data.status, license_id))
    if data.expiry_date:
        cursor.execute("UPDATE licenses SET expiry_date = ? WHERE id = ?", (data.expiry_date, license_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/admin/licenses/{license_id}")
async def delete_license(license_id: int, admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM licenses WHERE id = ?", (license_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/logs")
async def get_logs(limit: int = 50, admin = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM access_logs ORDER BY id DESC LIMIT ?", (limit,))
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return logs

# ==================== CLIENT PORTAL API ====================

@app.get("/api/client/my-apps")
async def get_my_apps(user = Depends(require_auth)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.id as license_id, l.license_key, l.status as license_status, l.expiry_date,
               l.hardware_lock_enabled, l.last_checked_at,
               s.title, s.app_code, s.version, s.description, s.download_url, s.file_size
        FROM licenses l
        JOIN softwares s ON l.software_id = s.id
        WHERE l.user_id = ?
        ORDER BY s.title ASC
    """, (user["id"],))
    apps = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return apps

# ==================== FILE DOWNLOADS ====================

@app.get("/download/file/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOADS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)

# ==================== CLIENT PYTHON SOFTWARE VERIFICATION API ====================

class VerifyLicensePayload(BaseModel):
    license_key: str
    app_code: str
    machine_id: str
    app_version: Optional[str] = "1.0.0"

@app.post("/api/v1/verify-license")
async def verify_license_endpoint(data: VerifyLicensePayload, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    conn = get_db()
    cursor = conn.cursor()

    def log_attempt(status_text: str, details: str):
        cursor.execute("""
            INSERT INTO access_logs (license_key, app_code, machine_id, ip_address, status, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data.license_key, data.app_code, data.machine_id, client_ip, status_text, details))
        conn.commit()

    # Find license matching key and app_code
    cursor.execute("""
        SELECT l.*, s.app_code, s.title, s.version as latest_version, s.download_url,
               u.full_name as client_name, u.company_name
        FROM licenses l
        JOIN softwares s ON l.software_id = s.id
        JOIN users u ON l.user_id = u.id
        WHERE l.license_key = ?
    """, (data.license_key.strip(),))
    lic = cursor.fetchone()

    if not lic:
        log_attempt("REJECTED_NOT_FOUND", "License key does not exist")
        conn.close()
        return JSONResponse(status_code=403, content={
            "valid": False,
            "status": "INVALID_KEY",
            "message": "Yeh License Key invalid hai ya register nahi hui."
        })

    # Check App Code Match
    if lic["app_code"] != data.app_code:
        log_attempt("REJECTED_APP_MISMATCH", f"Key is for {lic['app_code']} but app is {data.app_code}")
        conn.close()
        return JSONResponse(status_code=403, content={
            "valid": False,
            "status": "APP_MISMATCH",
            "message": f"Yeh license key '{lic['title']}' ke liye hai, is software ke liye nahi."
        })

    # Check Status
    if lic["status"] == "SUSPENDED":
        log_attempt("REJECTED_SUSPENDED", "License is suspended by admin")
        conn.close()
        return JSONResponse(status_code=403, content={
            "valid": False,
            "status": "SUSPENDED",
            "message": "Aapka software subscription suspend/block kardiya gaya hai. Admin se rabta karein."
        })

    # Check Expiry
    if lic["expiry_date"] != "LIFETIME":
        try:
            exp_date = datetime.strptime(lic["expiry_date"], "%Y-%m-%d").date()
            if date.today() > exp_date:
                cursor.execute("UPDATE licenses SET status = 'EXPIRED' WHERE id = ?", (lic["id"],))
                conn.commit()
                log_attempt("REJECTED_EXPIRED", f"Expired on {lic['expiry_date']}")
                conn.close()
                return JSONResponse(status_code=403, content={
                    "valid": False,
                    "status": "EXPIRED",
                    "message": f"Aapka software subscription {lic['expiry_date']} ko expire ho chuka hai. Renew karwayen."
                })
        except Exception:
            pass

    # Check Hardware / Machine ID Lock
    if lic["hardware_lock_enabled"]:
        if not lic["machine_id"]:
            # First time activation on client PC! Lock to this machine
            cursor.execute("UPDATE licenses SET machine_id = ? WHERE id = ?", (data.machine_id, lic["id"]))
            conn.commit()
        elif lic["machine_id"] != data.machine_id:
            log_attempt("BLOCKED_NEW_PC_ATTEMPT", f"ALREADY LOCKED TO: {lic['machine_id']} | UNAUTHORIZED ATTEMPT FROM: {data.machine_id}")
            conn.close()
            return JSONResponse(status_code=403, content={
                "valid": False,
                "status": "MACHINE_MISMATCH",
                "message": "🚫 PIRACY PROTECTION: Yeh License Key pehle hi kisi doosre computer par lock ho chuki hai! Ek License sirf ek computer ke liye hai. Yeh setup naye PC par nahi chal sakta."
            })

    # Update last checked timestamp
    cursor.execute("UPDATE licenses SET last_checked_at = datetime('now', 'localtime') WHERE id = ?", (lic["id"],))
    log_attempt("ALLOWED", "License verified successfully")
    conn.commit()
    conn.close()

    # Create signed/verified response
    return {
        "valid": True,
        "status": "ACTIVE",
        "client_name": lic["client_name"],
        "company_name": lic["company_name"],
        "software_title": lic["title"],
        "expiry_date": lic["expiry_date"],
        "latest_version": lic["latest_version"],
        "has_update": (data.app_version != lic["latest_version"]),
        "download_url": lic["download_url"],
        "verified_at": datetime.now().isoformat()
    }
