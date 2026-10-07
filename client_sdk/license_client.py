"""
Reusable Client SDK for Python Offline Softwares
------------------------------------------------
Yeh module aap apne kisi bhi offline Python software (Tkinter, PyQt, PyInstaller .exe) mein shamil kar sakte hain.

Key Features:
1. Anti-Piracy Machine ID (Locks software to customer's computer)
2. Online Server Verification via REST API
3. Offline Grace Period (Internet na hone par bhi pehle se verified app chalti rahegi)
4. Update Notifications (Batata hai agar server par new version aa gaya ho)
"""

import os
import sys
import json
import uuid
import hashlib
import platform
import subprocess
from datetime import datetime, timedelta
import urllib.request
import urllib.error

# Local token storage file (stored in AppData or current directory)
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".app_license_cache.json")

def get_machine_id() -> str:
    """
    Computes a tamper-proof hardware fingerprint combining:
    1. Motherboard / BIOS UUID
    2. CPU Processor ID
    3. Windows Registry MachineGuid
    Locks the software so it CANNOT be copied or run on any other PC.
    """
    system = platform.system()
    components = []

    if system == "Windows":
        # 1. Windows MachineGuid
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                if guid:
                    components.append(f"GUID:{guid.strip()}")
        except Exception:
            pass

        # 2. Motherboard / BIOS UUID
        try:
            output = subprocess.check_output("wmic csproduct get uuid", shell=True, stderr=subprocess.DEVNULL).decode()
            lines = [line.strip() for line in output.split('\n') if line.strip() and "UUID" not in line.upper()]
            if lines and lines[0] and lines[0] != "00000000-0000-0000-0000-000000000000":
                components.append(f"BIOS:{lines[0]}")
        except Exception:
            pass

        # 3. CPU Processor ID
        try:
            output = subprocess.check_output("wmic cpu get processorid", shell=True, stderr=subprocess.DEVNULL).decode()
            lines = [line.strip() for line in output.split('\n') if line.strip() and "PROCESSORID" not in line.upper()]
            if lines and lines[0]:
                components.append(f"CPU:{lines[0]}")
        except Exception:
            pass

    # Fallback if components empty
    if not components:
        components.append(f"NODE:{platform.node()}-{uuid.getnode()}-{platform.processor()}")

    raw_signature = "|".join(components)
    # Generate cryptographic SHA-256 hardware hash
    full_hash = hashlib.sha256(raw_signature.encode('utf-8')).hexdigest().upper()
    return f"HWID-{full_hash[:16]}"

def load_cached_license(app_code: str):
    """Loads previously saved offline validation token."""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(app_code)
    except Exception:
        return None

def save_cached_license(app_code: str, lic_data: dict):
    """Saves valid license token for offline use."""
    cache = {}
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}
    
    cache[app_code] = lic_data
    try:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

def verify_license(
    license_key: str,
    app_code: str,
    server_url: str = "http://127.0.0.1:8000",
    app_version: str = "1.0.0",
    offline_grace_days: int = 7
) -> tuple[bool, str, dict]:
    """
    Main Verification Function:
    
    Usage:
        is_valid, message, info = verify_license(
            license_key="LIC-XXXX-YYYY",
            app_code="retail_pos",
            server_url="https://your-server-url.com" # ya local URL
        )

    Returns:
        (True, "Access Granted", info_dict) agar valid ho.
        (False, "Error reason", {}) agar invalid/expired/mismatch ho.
    """
    license_key = license_key.strip()
    machine_id = get_machine_id()
    endpoint = f"{server_url.rstrip('/')}/api/v1/verify-license"

    payload = {
        "license_key": license_key,
        "app_code": app_code,
        "machine_id": machine_id,
        "app_version": app_version
    }

    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        endpoint,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        # Try connecting to server
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            if res_body.get("valid"):
                # Save cache for offline backup
                cache_payload = {
                    "license_key": license_key,
                    "machine_id": machine_id,
                    "client_name": res_body.get("client_name"),
                    "expiry_date": res_body.get("expiry_date"),
                    "last_online_verified": datetime.now().isoformat()
                }
                save_cached_license(app_code, cache_payload)
                return True, "Online Verification Successful", res_body
            else:
                return False, res_body.get("message", "License rejected"), res_body

    except urllib.error.HTTPError as e:
        # Server rejected with 403 or other status
        try:
            err_body = json.loads(e.read().decode('utf-8'))
            return False, err_body.get("message", "License validation failed"), err_body
        except Exception:
            return False, f"Server Error: HTTP {e.code}", {}

    except (urllib.error.URLError, TimeoutError, OSError):
        # Server unreachable (Client has no internet or server is offline)
        # Check offline cache grace period
        cached = load_cached_license(app_code)
        if cached:
            # Check machine ID match (Anti-Copy Protection)
            if cached.get("machine_id") != machine_id:
                return False, "🚫 ILLEGAL COPY DETECTED: Yeh software kisi doosre computer se copy kiya gaya hai. Is physical computer par chalne ki permission nahi hai!", {}
            
            # Check key match
            if cached.get("license_key") != license_key:
                return False, "🚫 License key mismatch in offline cache!", {}

            # Check grace period
            last_date_str = cached.get("last_online_verified")
            if last_date_str:
                last_date = datetime.fromisoformat(last_date_str)
                days_since = (datetime.now() - last_date).days
                if days_since <= offline_grace_days:
                    return True, f"Running in Offline Mode ({offline_grace_days - days_since} days remaining before next online check)", cached
                else:
                    return False, f"Offline grace period expired ({days_since} days since last check). Please connect to internet to verify license.", {}

        return False, "Server se rabta nahi ho saka aur koi valid offline cache mojood nahi hai. Pehli dafa internet connection zaroori hai.", {}
