// Global state
let clientsList = [];
let softwaresList = [];

// Init on load
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadDashboard();
    setupForms();

    document.getElementById('logout-btn').addEventListener('click', async () => {
        await fetch('/api/auth/logout', { method: 'POST' });
        window.location.href = '/';
    });
});

async function checkAuth() {
    try {
        const res = await fetch('/api/auth/me');
        if (!res.ok) {
            window.location.href = '/';
            return;
        }
        const user = await res.json();
        if (user.role !== 'admin') {
            window.location.href = '/portal';
            return;
        }
        document.getElementById('admin-user-display').textContent = user.full_name || user.username;
    } catch (e) {
        window.location.href = '/';
    }
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tabId));
    if (activeBtn) activeBtn.classList.add('active');

    const target = document.getElementById(tabId);
    if (target) target.classList.add('active');

    if (tabId === 'tab-logs') loadLogs();
}

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert(`Copied to clipboard: ${text}`);
    });
}

// Load all dashboard sections
async function loadDashboard() {
    loadStats();
    await loadClients();
    await loadSoftwares();
    await loadLicenses();
}

async function loadStats() {
    try {
        const res = await fetch('/api/admin/stats');
        if (res.ok) {
            const data = await res.json();
            document.getElementById('stat-clients').textContent = data.total_clients;
            document.getElementById('stat-softwares').textContent = data.total_softwares;
            document.getElementById('stat-licenses').textContent = data.active_licenses;
            document.getElementById('stat-checks').textContent = data.today_checks;
        }
    } catch (e) {
        console.error("Failed to load stats", e);
    }
}

// --- CLIENTS ---
async function loadClients() {
    const tbody = document.getElementById('clients-table-body');
    const clientSelect = document.getElementById('lic-client');
    try {
        const res = await fetch('/api/admin/clients');
        clientsList = await res.json();

        // Populate dropdown
        clientSelect.innerHTML = '<option value="">Choose a customer...</option>';
        clientsList.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = `${c.full_name} (${c.company_name || c.username})`;
            clientSelect.appendChild(opt);
        });

        if (clientsList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2rem;">Koi customer nahi mila. "Add New Client" par click karein.</td></tr>';
            return;
        }

        tbody.innerHTML = clientsList.map(c => `
            <tr>
                <td><strong>#${c.id}</strong></td>
                <td><strong style="color: #fff;">${escapeHtml(c.full_name)}</strong></td>
                <td>${escapeHtml(c.company_name || 'N/A')}</td>
                <td><span class="key-box" style="font-size: 0.8rem;">${escapeHtml(c.username)}</span></td>
                <td>${escapeHtml(c.phone || 'N/A')}</td>
                <td><span class="badge badge-active">${c.total_licenses} Apps</span></td>
                <td>${c.created_at ? c.created_at.split(' ')[0] : ''}</td>
                <td>
                    <div style="display: flex; gap: 4px;">
                        <button class="btn btn-outline btn-sm" style="color: #38bdf8; font-size: 0.75rem; padding: 3px 7px;" onclick="openResetClientPassword(${c.id}, '${escapeHtml(c.full_name)}', '${escapeHtml(c.username)}', '${escapeHtml(c.plain_password || '')}')">🔑 Pass</button>
                        <button class="btn btn-danger btn-sm" style="font-size: 0.75rem; padding: 3px 7px;" onclick="deleteClient(${c.id})">Delete</button>
                    </div>
                </td>
            </tr>
        `).join('');

    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: red;">Error loading clients</td></tr>';
    }
}

async function deleteClient(id) {
    if (!confirm("Kya aap waqai is client ko delete karna chahte hain? Tamam licenses bhi khatam ho jayenge.")) return;
    const res = await fetch(`/api/admin/clients/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadDashboard();
    } else {
        alert("Delete failed!");
    }
}

// --- SOFTWARES ---
async function loadSoftwares() {
    const tbody = document.getElementById('softwares-table-body');
    const softSelect = document.getElementById('lic-software');
    try {
        const res = await fetch('/api/admin/softwares');
        softwaresList = await res.json();

        // Populate dropdown
        softSelect.innerHTML = '<option value="">Choose software...</option>';
        softwaresList.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = `${s.title} (v${s.version}) [${s.app_code}]`;
            softSelect.appendChild(opt);
        });

        if (softwaresList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">Koi software register nahi hua. "Register New Software" par click karein.</td></tr>';
            return;
        }

        tbody.innerHTML = softwaresList.map(s => `
            <tr>
                <td><span class="key-box" style="font-size: 0.8rem; color: #a78bfa;">${escapeHtml(s.app_code)}</span></td>
                <td><strong style="color: #fff;">${escapeHtml(s.title)}</strong></td>
                <td><span class="app-version">v${escapeHtml(s.version)}</span></td>
                <td>
                    ${s.download_url ? `<a href="${s.download_url}" target="_blank" class="btn btn-outline btn-sm">Download Source</a>` : '<span style="color: var(--text-muted);">No Link</span>'}
                    ${s.file_size ? `<small style="color: var(--text-muted); display: block;">${s.file_size}</small>` : ''}
                </td>
                <td><span class="badge badge-active">${s.assigned_count} Assigned</span></td>
                <td style="color: var(--text-muted); max-width: 250px;">${escapeHtml(s.description || 'No description')}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="deleteSoftware(${s.id})">Delete</button>
                </td>
            </tr>
        `).join('');

    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: red;">Error loading softwares</td></tr>';
    }
}

async function deleteSoftware(id) {
    if (!confirm("Kya aap waqai is software ko delete karna chahte hain?")) return;
    const res = await fetch(`/api/admin/softwares/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadDashboard();
    } else {
        alert("Delete failed!");
    }
}

// --- LICENSES ---
async function loadLicenses() {
    const tbody = document.getElementById('licenses-table-body');
    try {
        const res = await fetch('/api/admin/licenses');
        const licenses = await res.json();

        if (licenses.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2rem;">Abhi koi license generate nahi hua. "Generate License Key" par click karein.</td></tr>';
            return;
        }

        tbody.innerHTML = licenses.map(l => {
            const isSuspended = l.status === 'SUSPENDED';
            const isExpired = l.status === 'EXPIRED';
            const badgeClass = isSuspended ? 'badge-suspended' : (isExpired ? 'badge-expired' : 'badge-active');

            return `
                <tr>
                    <td>
                        <span class="key-box">
                            ${l.license_key}
                            <span class="copy-btn" onclick="copyToClipboard('${l.license_key}')" title="Copy Key">📋</span>
                        </span>
                    </td>
                    <td>
                        <strong>${escapeHtml(l.client_name)}</strong>
                        <small style="display:block; color: var(--text-muted);">${escapeHtml(l.company_name || l.client_username)}</small>
                    </td>
                    <td>
                        <strong style="color: #67e8f9;">${escapeHtml(l.software_title)}</strong>
                        <small style="display:block; color: var(--text-muted);">${l.app_code}</small>
                    </td>
                    <td><span class="badge ${badgeClass}">${l.status}</span></td>
                    <td>${l.expiry_date === 'LIFETIME' ? '<span style="color: #34d399; font-weight:600;">Lifetime</span>' : l.expiry_date}</td>
                    <td>
                        ${l.machine_id ? `
                            <code style="font-size:0.75rem; color:#a5b4fc; display:block; max-width:140px; overflow:hidden; text-overflow:ellipsis;">${l.machine_id}</code>
                            <button class="btn btn-outline btn-sm" style="margin-top:4px; font-size:0.7rem; padding: 2px 6px;" onclick="resetMachineLock(${l.id})">Reset Lock</button>
                        ` : '<span style="color: var(--text-muted); font-size: 0.8rem;">Not activated yet</span>'}
                    </td>
                    <td style="font-size: 0.8rem; color: var(--text-muted);">${l.last_checked_at ? l.last_checked_at : 'Never'}</td>
                    <td>
                        <div style="display: flex; gap: 4px;">
                            ${isSuspended ? 
                                `<button class="btn btn-outline btn-sm" style="color: #34d399;" onclick="toggleLicenseStatus(${l.id}, 'ACTIVE')">Activate</button>` :
                                `<button class="btn btn-outline btn-sm" style="color: #f87171;" onclick="toggleLicenseStatus(${l.id}, 'SUSPENDED')">Suspend</button>`
                            }
                            <button class="btn btn-danger btn-sm" onclick="deleteLicense(${l.id})">&times;</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: red;">Error loading licenses</td></tr>';
    }
}

async function toggleLicenseStatus(id, newStatus) {
    const res = await fetch(`/api/admin/licenses/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) loadLicenses();
}

async function resetMachineLock(id) {
    if (!confirm("Is license ka machine lock reset kar dein? Ab yeh kisi naye PC par bind ho sakega.")) return;
    const res = await fetch(`/api/admin/licenses/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reset_machine: true })
    });
    if (res.ok) {
        alert("Machine lock reset hogaya!");
        loadLicenses();
    }
}

async function deleteLicense(id) {
    if (!confirm("Kya aap yeh license key delete karna chahte hain?")) return;
    const res = await fetch(`/api/admin/licenses/${id}`, { method: 'DELETE' });
    if (res.ok) loadLicenses();
}

// --- LOGS ---
async function loadLogs() {
    const tbody = document.getElementById('logs-table-body');
    try {
        const res = await fetch('/api/admin/logs');
        const logs = await res.json();

        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">Abhi koi verification log nahi hai.</td></tr>';
            return;
        }

        tbody.innerHTML = logs.map(log => {
            const isAllowed = log.status === 'ALLOWED';
            return `
                <tr>
                    <td style="font-size: 0.8rem; color: var(--text-muted);">${log.created_at}</td>
                    <td><span class="key-box" style="font-size: 0.75rem;">${escapeHtml(log.app_code || 'N/A')}</span></td>
                    <td style="font-family: monospace; font-size: 0.8rem;">${log.license_key || 'N/A'}</td>
                    <td style="font-size: 0.8rem;">${log.ip_address}</td>
                    <td style="font-size: 0.75rem; color: #a5b4fc; max-width: 140px; overflow: hidden; text-overflow: ellipsis;">${log.machine_id || 'N/A'}</td>
                    <td>
                        <span class="badge ${isAllowed ? 'badge-active' : 'badge-suspended'}">
                            ${log.status}
                        </span>
                    </td>
                    <td style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(log.details || '')}</td>
                </tr>
            `;
        }).join('');

    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: red;">Error loading logs</td></tr>';
    }
}

// --- FORM HANDLERS ---
function setupForms() {
    // Add Client
    document.getElementById('form-add-client').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            full_name: document.getElementById('client-name').value.trim(),
            company_name: document.getElementById('client-company').value.trim(),
            phone: document.getElementById('client-phone').value.trim(),
            username: document.getElementById('client-username').value.trim(),
            password: document.getElementById('client-password').value
        };

        const res = await fetch('/api/admin/clients', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            closeModal('modal-add-client');
            e.target.reset();
            loadDashboard();
        } else {
            const err = await res.json();
            alert(err.detail || 'Error adding client');
        }
    });

    // Add Software
    document.getElementById('form-add-software').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('title', document.getElementById('soft-title').value.trim());
        formData.append('app_code', document.getElementById('soft-code').value.trim());
        formData.append('version', document.getElementById('soft-version').value.trim());
        formData.append('description', document.getElementById('soft-desc').value.trim());
        formData.append('download_url', document.getElementById('soft-url').value.trim());

        const fileInput = document.getElementById('soft-file');
        if (fileInput.files.length > 0) {
            formData.append('file', fileInput.files[0]);
        }

        const res = await fetch('/api/admin/softwares', {
            method: 'POST',
            body: formData
        });

        if (res.ok) {
            closeModal('modal-add-software');
            e.target.reset();
            loadDashboard();
        } else {
            const err = await res.json();
            alert(err.detail || 'Error registering software');
        }
    });

    // Generate License
    document.getElementById('form-add-license').addEventListener('submit', async (e) => {
        e.preventDefault();
        const expiryVal = document.getElementById('lic-expiry').value;
        const payload = {
            user_id: parseInt(document.getElementById('lic-client').value),
            software_id: parseInt(document.getElementById('lic-software').value),
            expiry_date: expiryVal ? expiryVal : "LIFETIME",
            hardware_lock_enabled: parseInt(document.getElementById('lic-hardware-lock').value),
            notes: document.getElementById('lic-notes').value.trim()
        };

        const res = await fetch('/api/admin/licenses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const data = await res.json();
            closeModal('modal-add-license');
            e.target.reset();
            alert(`Naya License Key generate hogaya:\n${data.license_key}`);
            loadDashboard();
        } else {
            alert('Error generating license');
        }
    });

    // Admin Change Password
    document.getElementById('form-admin-settings').addEventListener('submit', async (e) => {
        e.preventDefault();
        const old_password = document.getElementById('admin-old-pass').value;
        const new_password = document.getElementById('admin-new-pass').value;
        const confirm_pass = document.getElementById('admin-confirm-pass').value;

        if (new_password !== confirm_pass) {
            alert("Naya password aur confirm password match nahi karte!");
            return;
        }

        const res = await fetch('/api/auth/change-password', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_password, new_password })
        });

        if (res.ok) {
            alert("Admin password kamyabi se tabdeel hogaya!");
            closeModal('modal-admin-settings');
            e.target.reset();
        } else {
            const err = await res.json();
            alert(err.detail || 'Password update failed!');
        }
    });

    // Reset Client Password
    document.getElementById('form-client-password').addEventListener('submit', async (e) => {
        e.preventDefault();
        const client_id = document.getElementById('reset-client-id').value;
        const new_password = document.getElementById('client-new-pass').value;

        const res = await fetch(`/api/admin/clients/${client_id}/password`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_password })
        });

        if (res.ok) {
            alert("Customer ka password kamyabi se update hogaya!");
            closeModal('modal-client-password');
            e.target.reset();
        } else {
            const err = await res.json();
            alert(err.detail || 'Error updating client password!');
        }
    });
}

function openResetClientPassword(clientId, clientName, clientUsername, currentPass) {
    document.getElementById('reset-client-id').value = clientId;
    document.getElementById('reset-client-name-display').textContent = `Customer: ${clientName} (@${clientUsername})`;
    document.getElementById('client-new-pass').value = '';
    const passDisplay = document.getElementById('client-current-pass-display');
    if (currentPass && currentPass !== 'null' && currentPass !== '') {
        passDisplay.textContent = currentPass;
        passDisplay.style.color = '#fbbf24';
    } else {
        passDisplay.textContent = 'Password stored nahi hai (purana account)';
        passDisplay.style.color = '#64748b';
    }
    openModal('modal-client-password');
}

function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/[&<>"']/g, function(m) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        }[m];
    });
}
