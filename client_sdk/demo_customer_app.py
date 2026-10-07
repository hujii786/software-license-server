"""
Sample Offline Python Desktop Application
Demonstrates how to integrate the License Verification SDK into any Python desktop app.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

# Import the license client SDK
sys.path.insert(0, os.path.dirname(__file__))
from license_client import verify_license, get_machine_id

APP_CODE = "retail_pos"
APP_TITLE = "Super POS Retail Management (Offline App)"
APP_VERSION = "1.0.0"
# Public Live URL (Cloudflare Tunnel)
SERVER_URL = "https://expo-dealers-hoped-duty.trycloudflare.com"
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "client_license.txt")

class OfflineDemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} - v{APP_VERSION}")
        self.root.geometry("680x520")
        self.root.configure(bg="#0f172a")

        # Check for existing saved license key
        saved_key = self.load_saved_key()

        if saved_key:
            self.attempt_startup(saved_key)
        else:
            self.show_activation_screen()

    def load_saved_key(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return f.read().strip()
            except Exception:
                pass
        return None

    def save_key(self, key):
        with open(CONFIG_FILE, "w") as f:
            f.write(key.strip())

    def show_activation_screen(self):
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.root, bg="#1e293b", padx=30, pady=30, relief="flat", bd=1)
        frame.place(relx=0.5, rely=0.5, anchor="center", width=550)

        # Title
        tk.Label(frame, text="🔒 Software Activation Required", font=("Arial", 16, "bold"), fg="#f8fafc", bg="#1e293b").pack(pady=(0, 5))
        tk.Label(frame, text="Yeh offline software chalane ke liye apni License Key darj karein.", font=("Arial", 10), fg="#94a3b8", bg="#1e293b").pack(pady=(0, 20))

        # Hardware ID display
        machine_id = get_machine_id()
        id_frame = tk.Frame(frame, bg="#0f172a", padx=10, pady=8)
        id_frame.pack(fill="x", pady=(0, 15))
        tk.Label(id_frame, text="Aapke Computer ki Hardware ID:", font=("Arial", 9), fg="#64748b", bg="#0f172a").pack(anchor="w")
        tk.Label(id_frame, text=machine_id, font=("Consolas", 10, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w")

        # License Key Input
        tk.Label(frame, text="License Key (Server Portal se mili hui):", font=("Arial", 10, "bold"), fg="#e2e8f0", bg="#1e293b").pack(anchor="w", pady=(0, 5))
        self.key_entry = tk.Entry(frame, font=("Consolas", 12), bg="#0f172a", fg="#a5b4fc", insertbackground="white", relief="solid", bd=1)
        self.key_entry.pack(fill="x", ipady=8, pady=(0, 20))
        self.key_entry.focus()

        # Status Label
        self.status_lbl = tk.Label(frame, text="", font=("Arial", 9), fg="#f87171", bg="#1e293b")
        self.status_lbl.pack(pady=(0, 10))

        # Activate Button
        btn = tk.Button(frame, text="Verify & Activate Software 🚀", font=("Arial", 11, "bold"), bg="#6366f1", fg="white", activebackground="#4f46e5", activeforeground="white", relief="flat", cursor="hand2", command=self.on_activate_click)
        btn.pack(fill="x", ipady=8)

    def on_activate_click(self):
        key = self.key_entry.get().strip()
        if not key:
            self.status_lbl.config(text="Barah-e-karam License Key enter karein!", fg="#f87171")
            return

        self.status_lbl.config(text="Server se verify ho raha hai... Please wait.", fg="#38bdf8")
        self.root.update()

        valid, msg, info = verify_license(key, APP_CODE, server_url=SERVER_URL, app_version=APP_VERSION)
        if valid:
            self.save_key(key)
            self.show_main_app(info)
        else:
            self.status_lbl.config(text=f"❌ {msg}", fg="#f87171")

    def attempt_startup(self, key):
        valid, msg, info = verify_license(key, APP_CODE, server_url=SERVER_URL, app_version=APP_VERSION)
        if valid:
            self.show_main_app(info)
        else:
            # If failed, show alert and go to activation screen
            messagebox.showerror("License Error", f"Software start nahi ho saka:\n\n{msg}")
            self.show_activation_screen()

    def show_main_app(self, lic_info):
        # Clear window and load the offline software dashboard
        for widget in self.root.winfo_children():
            widget.destroy()

        # Top Bar
        top_bar = tk.Frame(self.root, bg="#1e293b", padx=20, pady=15)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="🛒 " + APP_TITLE, font=("Arial", 14, "bold"), fg="#f8fafc", bg="#1e293b").pack(side="left")
        
        status_text = "🟢 Active License" if lic_info.get("status") == "ACTIVE" else "🟡 Offline Mode"
        tk.Label(top_bar, text=status_text, font=("Arial", 9, "bold"), fg="#34d399", bg="#1e293b").pack(side="right")

        # License Info Banner
        info_frame = tk.Frame(self.root, bg="#111827", padx=20, pady=10)
        info_frame.pack(fill="x", padx=20, pady=15)
        
        c_name = lic_info.get("client_name") or "Registered Client"
        c_comp = lic_info.get("company_name") or ""
        exp = lic_info.get("expiry_date") or "Lifetime"

        tk.Label(info_frame, text=f"Licensed to: {c_name} {f'({c_comp})' if c_comp else ''}", font=("Arial", 10, "bold"), fg="#e2e8f0", bg="#111827").pack(anchor="w")
        tk.Label(info_frame, text=f"Validity: {exp} | Hardware Fingerprint: {get_machine_id()}", font=("Arial", 9), fg="#94a3b8", bg="#111827").pack(anchor="w", pady=(3, 0))

        # Check for update alert
        if lic_info.get("has_update"):
            update_frame = tk.Frame(self.root, bg="#312e81", padx=15, pady=8)
            update_frame.pack(fill="x", padx=20, pady=(0, 10))
            tk.Label(update_frame, text=f"⚡ New Update Available (v{lic_info.get('latest_version')})! Customer Portal se download karein.", font=("Arial", 9, "bold"), fg="#c7d2fe", bg="#312e81").pack()

        # Software Mock Content Area (Simulating offline POS actions)
        content_frame = tk.Frame(self.root, bg="#0f172a", padx=20, pady=10)
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tk.Label(content_frame, text="Software Functions (Simulated Offline Desktop App)", font=("Arial", 12, "bold"), fg="#93c5fd", bg="#0f172a").pack(anchor="w", pady=(0, 10))

        # Sample POS buttons
        btn_grid = tk.Frame(content_frame, bg="#0f172a")
        btn_grid.pack(fill="x", pady=10)

        buttons = [
            ("➕ New Sale Invoice", "#059669"),
            ("📦 Product Inventory", "#0284c7"),
            ("📊 Daily Sales Report", "#7c3aed"),
            ("⚙️ Software Settings", "#475569")
        ]

        for text, col in buttons:
            b = tk.Button(btn_grid, text=text, font=("Arial", 10, "bold"), bg=col, fg="white", activebackground=col, relief="flat", padx=15, pady=12, cursor="hand2")
            b.pack(side="left", padx=5, expand=True, fill="x")

        # Log area
        tk.Label(content_frame, text="Activity Log:", font=("Arial", 10, "bold"), fg="#64748b", bg="#0f172a").pack(anchor="w", pady=(15, 5))
        log_box = tk.Text(content_frame, height=6, bg="#1e293b", fg="#cbd5e1", font=("Consolas", 9), relief="flat")
        log_box.pack(fill="both", expand=True)
        log_box.insert("end", f"[*] Software booted successfully.\n[*] License verified with Server ({SERVER_URL}).\n[*] Hardware ID locked: {get_machine_id()}\n[*] Ready for offline store sales.\n")
        log_box.config(state="disabled")

        # Bottom buttons
        bottom_bar = tk.Frame(self.root, bg="#0f172a", padx=20, pady=10)
        bottom_bar.pack(fill="x")
        
        tk.Button(bottom_bar, text="Change / Re-enter License Key", font=("Arial", 9), bg="#334155", fg="#f1f5f9", relief="flat", command=self.reset_key).pack(side="left")
        tk.Button(bottom_bar, text="Exit App", font=("Arial", 9), bg="#ef4444", fg="white", relief="flat", command=self.root.quit).pack(side="right")

    def reset_key(self):
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        self.show_activation_screen()

if __name__ == "__main__":
    root = tk.Tk()
    app = OfflineDemoApp(root)
    root.mainloop()
