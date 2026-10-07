# Personal Customer Software Server & Licensing Hub ⚡

Yeh aik complete **Customer Management, Software Distribution, aur Anti-Piracy Licensing System** hai jo khas tor par **Python Offline Softwares** (Tkinter, PyQt, PyInstaller `.exe` apps) ke liye banaya gaya hai.

---

## 🌟 Key Features

1. **Master Admin Dashboard:**
   - Naye customers/clients add karna.
   - Python softwares register karna aur unke `.exe`/`.zip` setup files upload ya link karna.
   - **License Keys** generate karna (Lifetime, 1 Year, 30 Days Trial).
   - **Machine Hardware Lock:** Software sirf usi customer ke computer par chalega (Hardware ID binding).
   - Kisi bhi waqt 1 click se license **Active**, **Suspend**, ya **Reset Lock** karna.
   - **Live Verification Logs:** Real-time pata chalega kis client ne kab aur kis computer se software open kiya.

2. **Customer Download Portal:**
   - Har client apne username aur password se login karega.
   - Customer ko sirf uske khareeday hue softwares nazar aayenge.
   - Latest Setup download karne ka direct button.
   - Unki License Key aur subscription expiry date ka display with 1-click copy.

3. **Offline Python Client SDK (`license_client.py`):**
   - Reusable Python module jo aap apne kisi bhi offline project mein sirf 3-4 lines mein import kar sakte hain.
   - **Offline Grace Period:** Agar customer ka internet band ho, tab bhi software bina rukawat chalta rahega.
   - **Auto Update Notifications:** Agar server par naya version upload ho tou software alert dikhayega.

---

## 🚀 Server Chalane Ka Tareeqa (How to Run)

### Tareeqa 1: 1-Click Batch File
Aap simply `run_server.bat` file par double click karein.

### Tareeqa 2: Terminal / PowerShell se
```powershell
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

Server chalne ke baad browser mein open karein:
- **Login Screen:** [http://localhost:8000](http://localhost:8000)
- **Admin Dashboard:** [http://localhost:8000/admin](http://localhost:8000/admin)
- **Customer Portal:** [http://localhost:8000/portal](http://localhost:8000/portal)

### Default Admin Login:
- **Username:** `admin`
- **Password:** `admin123`

---

## 🛠️ Apne Python Software mein Server kaise Link karein?

Aap apne kisi bhi Python desktop project mein `client_sdk/license_client.py` file copy karein aur apne main script ke start mein yeh code likhein:

```python
from license_client import verify_license

# Software open hone par check:
is_valid, msg, info = verify_license(
    license_key="LIC-XXXX-YYYY-ZZZZ", # Jo client ne enter ki
    app_code="retail_pos",            # Jo code aapne server par rakha hai
    server_url="http://localhost:8000" # Ya live free Cloudflare URL
)

if not is_valid:
    print("Software chalne ki ijazat nahi hai:", msg)
    # yahan error popup dikha kar exit() kar dein
    exit()

print("License verified! Welcome", info.get("client_name"))
# yahan aapka software normal run hoga
```

---

## 🧪 Demo Test Karne Ka Tareeqa

1. Server start karein (`run_server.bat`).
2. Browser mein [http://localhost:8000/admin](http://localhost:8000/admin) open karein.
3. Naya client banayein (e.g. `ali_pharmacy`).
4. Naya software register karein (App Code: `retail_pos`).
5. License Key generate karein.
6. Ab demo app chalayein:
   ```powershell
   python client_sdk\demo_customer_app.py
   ```
7. App mein wahi license key paste karein aur **Verify & Activate** par click karein.
8. Admin panel mein jaakar dekhein ke live log mein entry aa chuki hogi aur machine ID lock ho chuki hogi!

---

## 🌐 100% Free Internet URL Kaise Banayein?
Agar aap chahte hain ke clients internet ke zariye aapke computer se connect ho saken, tou [setup_free_tunnel.md](file:///d:/project/all%20softwear%20server/setup_free_tunnel.md) parhein.
