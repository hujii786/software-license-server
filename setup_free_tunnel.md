# 100% Free Internet Setup Guide (Cloudflare Tunnel)

Aapka server local computer par port `8000` par chalta hai. Agar aap chahte hain ke **puri dunya mein aapke customers kahin se bhi** aapke server se connect ho saken (software download karein ya license verify karein) bina kisi hosting ya domain fees ke, tou yeh tareeqa istemal karein:

---

## Method 1: Cloudflare Tunnel (Recommended - 100% Free & Unlimited)

Cloudflare Tunnel bilkul free hai, iske liye koi port forwarding ya router settings nahi karni parti, aur aapko aik secure `https://` link milta hai.

### Step 1: Cloudflared Download Karein
1. [Cloudflared for Windows](https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi) download aur install karein (ya exe download karein).

### Step 2: 1-Command mein Free URL Hasil Karein
Command Prompt (cmd) ya PowerShell open karein aur yeh command chalayein:
```powershell
cloudflared tunnel --url http://localhost:8000
```

### Result:
Aapko screen par aik free link milega, misal ke tor par:
```text
https://random-words-123.trycloudflare.com
```

Ab aapke customers is link ke zariye apna portal open kar sakte hain, aur aapke Python desktop softwares mein `SERVER_URL` is link ko set kar sakte hain!

---

## Method 2: Free Cloud Hosting (Agar computer har waqt on na rakhna ho)

Agar aap chahte hain ke aapka laptop/PC band bhi ho tab bhi server 24/7 internet par chalta rahe:

1. **Render.com (Free Tier):**
   - GitHub par yeh project push karein.
   - Render.com par "New Web Service" banayein.
   - Start Command: `uvicorn server.app:app --host 0.0.0.0 --port 10000`
   - Aapko free domain mil jayega jaise: `https://my-software-hub.onrender.com`.

2. **PythonAnywhere (Free Tier):**
   - Free Python hosting par direct `server/app.py` deploy kar sakte hain.

---

## Software mein Server URL Kaise Badlein?

Aapke Python software (`demo_customer_app.py` ya aapke real project) mein:
```python
# Agar testing kar rahe hain:
SERVER_URL = "http://127.0.0.1:8000"

# Jab live internet par daal dein:
SERVER_URL = "https://your-tunnel-url.trycloudflare.com"
```
Sirf yeh aik line change karne se aapka offline software seedha aapke live server se verify hona shuru ho jayega!
