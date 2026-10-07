"""
Automated test script to verify all server endpoints, licensing verification, and anti-piracy logic.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from server.app import app
from server.database import init_db

def run_tests():
    print("=== 1. Initializing Database ===")
    init_db()

    client = TestClient(app)

    print("\n=== 2. Testing Admin Login ===")
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Admin login successful. Token acquired.")

    print("\n=== 3. Testing Adding Client ===")
    res = client.post("/api/admin/clients", headers=headers, json={
        "full_name": "Dr. Tariq Khan",
        "company_name": "Shifa Clinic",
        "phone": "03001234567",
        "username": "dr_tariq",
        "password": "client_password123",
        "email": "tariq@shifa.com"
    })
    assert res.status_code == 200, f"Client creation failed: {res.text}"
    print("[OK] Client 'dr_tariq' created successfully.")

    # Get client ID
    res = client.get("/api/admin/clients", headers=headers)
    clients = res.json()
    tariq = next(c for c in clients if c["username"] == "dr_tariq")
    client_id = tariq["id"]

    print("\n=== 4. Testing Registering Software ===")
    res = client.post("/api/admin/softwares", headers=headers, data={
        "title": "Clinic Patient Management",
        "app_code": "clinic_pms",
        "version": "1.0.0",
        "description": "Offline Doctor OPD & Prescription Software",
        "download_url": "https://example.com/clinic_setup.exe"
    })
    assert res.status_code == 200, f"Software creation failed: {res.text}"
    print("[OK] Software 'clinic_pms' registered.")

    # Get software ID
    res = client.get("/api/admin/softwares", headers=headers)
    softs = res.json()
    clinic_soft = next(s for s in softs if s["app_code"] == "clinic_pms")
    soft_id = clinic_soft["id"]

    print("\n=== 5. Testing License Key Generation ===")
    res = client.post("/api/admin/licenses", headers=headers, json={
        "user_id": client_id,
        "software_id": soft_id,
        "expiry_date": "LIFETIME",
        "hardware_lock_enabled": 1,
        "notes": "Paid full license"
    })
    assert res.status_code == 200, f"License creation failed: {res.text}"
    lic_key = res.json()["license_key"]
    print(f"[OK] Generated License Key: {lic_key}")

    print("\n=== 6. Testing License Verification API (First Activation on PC 1) ===")
    machine_1 = "PC-HARDWARE-UUID-AAAA-1111"
    res = client.post("/api/v1/verify-license", json={
        "license_key": lic_key,
        "app_code": "clinic_pms",
        "machine_id": machine_1,
        "app_version": "1.0.0"
    })
    assert res.status_code == 200, f"Verification failed: {res.text}"
    data = res.json()
    assert data["valid"] is True
    assert data["status"] == "ACTIVE"
    print("[OK] License successfully activated and locked to Machine 1!")

    print("\n=== 7. Testing Anti-Piracy Lock (Attempting to run on PC 2) ===")
    machine_2 = "PC-HARDWARE-UUID-BBBB-2222"
    res = client.post("/api/v1/verify-license", json={
        "license_key": lic_key,
        "app_code": "clinic_pms",
        "machine_id": machine_2,
        "app_version": "1.0.0"
    })
    assert res.status_code == 403, "Should fail on unauthorized machine"
    assert res.json()["status"] == "MACHINE_MISMATCH"
    print("[OK] Machine Mismatch Anti-Piracy successfully blocked PC 2!")

    print("\n=== 8. Testing Client Portal (Login as Customer) ===")
    res = client.post("/api/auth/login", json={"username": "dr_tariq", "password": "client_password123"})
    assert res.status_code == 200
    client_token = res.json()["token"]
    c_headers = {"Authorization": f"Bearer {client_token}"}

    res = client.get("/api/client/my-apps", headers=c_headers)
    assert res.status_code == 200
    my_apps = res.json()
    assert len(my_apps) == 1
    assert my_apps[0]["license_key"] == lic_key
    print("[OK] Customer Portal successfully displayed assigned software and license key!")

    print("\n=== 9. Testing Remote Suspension ===")
    # Get license id
    res = client.get("/api/admin/licenses", headers=headers)
    lic_id = next(l["id"] for l in res.json() if l["license_key"] == lic_key)
    # Suspend
    res = client.put(f"/api/admin/licenses/{lic_id}", headers=headers, json={"status": "SUSPENDED"})
    assert res.status_code == 200

    # Try verifying again from machine 1
    res = client.post("/api/v1/verify-license", json={
        "license_key": lic_key,
        "app_code": "clinic_pms",
        "machine_id": machine_1,
        "app_version": "1.0.0"
    })
    assert res.status_code == 403
    assert res.json()["status"] == "SUSPENDED"
    print("[OK] Remote Suspension instantly deactivated client software!")

    print("\n*** ALL TESTS PASSED SUCCESSFULLY! 100% WORKING! ***")

if __name__ == "__main__":
    run_tests()
