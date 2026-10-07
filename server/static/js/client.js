document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadMyApps();

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
        document.getElementById('client-user-display').textContent = user.full_name || user.username;
        document.getElementById('welcome-name').textContent = user.full_name || user.username;
        if (user.company_name) {
            document.getElementById('welcome-company').textContent = `${user.company_name} - Yahan aapke tamam khareeday hue Python offline softwares, unke latest setup files, aur activation keys mojood hain.`;
        }
    } catch (e) {
        window.location.href = '/';
    }
}

async function loadMyApps() {
    const container = document.getElementById('apps-container');
    try {
        const res = await fetch('/api/client/my-apps');
        if (!res.ok) {
            container.innerHTML = '<div class="glass" style="padding: 2rem; text-align:center; color: red;">Failed to load applications.</div>';
            return;
        }

        const apps = await res.json();
        if (apps.length === 0) {
            container.innerHTML = `
                <div class="glass" style="padding: 3rem; text-align: center; grid-column: 1 / -1; color: var(--text-muted);">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">📦</div>
                    <h3>Abhi aapko koi software assign nahi hua</h3>
                    <p style="margin-top: 0.5rem; font-size: 0.9rem;">Admin se rabta karein taake wo aapke account par software activate kar sakein.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = apps.map(app => {
            const isSuspended = app.license_status === 'SUSPENDED';
            const isExpired = app.license_status === 'EXPIRED';
            const badgeClass = isSuspended ? 'badge-suspended' : (isExpired ? 'badge-expired' : 'badge-active');

            return `
                <div class="glass app-card">
                    <div>
                        <div class="app-header">
                            <div>
                                <h3 class="app-title">${escapeHtml(app.title)}</h3>
                                <span class="app-version">v${escapeHtml(app.version)}</span>
                            </div>
                            <span class="badge ${badgeClass}">${app.license_status}</span>
                        </div>

                        <p class="app-desc">
                            ${escapeHtml(app.description || 'Offline Desktop Application tailored for your business needs.')}
                        </p>

                        <div style="margin-bottom: 1.25rem;">
                            <label style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600; display: block; margin-bottom: 0.35rem;">
                                Your License Key:
                            </label>
                            <span class="key-box" style="font-size: 0.9rem; width: 100%; justify-content: space-between;">
                                <span>${app.license_key}</span>
                                <span class="copy-btn" onclick="copyKey('${app.license_key}')" title="Copy Key">📋 Copy</span>
                            </span>
                        </div>

                        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                            <span>Subscription Expiry:</span>
                            <strong style="color: ${app.expiry_date === 'LIFETIME' ? '#34d399' : '#f8fafc'};">
                                ${app.expiry_date === 'LIFETIME' ? 'Lifetime Validity' : app.expiry_date}
                            </strong>
                        </div>

                        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-muted);">
                            <span>PC Hardware Lock:</span>
                            <span style="color: ${app.hardware_lock_enabled ? '#38bdf8' : '#94a3b8'};">
                                ${app.hardware_lock_enabled ? 'Locked to 1 PC' : 'Multi-device'}
                            </span>
                        </div>
                    </div>

                    <div class="app-footer">
                        <span style="font-size: 0.8rem; color: var(--text-muted);">
                            ${app.file_size ? `Size: ${app.file_size}` : 'Ready to install'}
                        </span>
                        ${app.download_url ? `
                            <a href="${app.download_url}" target="_blank" class="btn btn-primary btn-sm">
                                ⬇️ Download Setup
                            </a>
                        ` : `
                            <button class="btn btn-outline btn-sm" disabled style="opacity: 0.5;">
                                No Download Link
                            </button>
                        `}
                    </div>
                </div>
            `;
        }).join('');

    } catch (e) {
        container.innerHTML = '<div class="glass" style="padding: 2rem; text-align:center; color: red;">Network error loading apps.</div>';
    }
}

function copyKey(key) {
    navigator.clipboard.writeText(key).then(() => {
        alert(`License Key copied:\n${key}\n\nApne software ke prompt mein paste karein.`);
    });
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
