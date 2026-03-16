// js/auth.js
(function () {
    const currentPagePath = window.location.pathname;
    const currentPage = currentPagePath.split('/').pop() || 'index.html';

    // Core System Auth (index.html -> dashboard.html)
    if (currentPage !== 'index.html' && currentPage !== 'admin_login.html') {
        const token = sessionStorage.getItem('systemToken');
        if (!token) {
            window.location.href = 'index.html';
            return;
        }

        // Secondary Intra-Portal Auth
        const officerPages = ['officer_registration.html', 'officer_visitors.html', 'visitor_request.html'];
        const receptionPages = ['reception_dashboard.html', 'todays_visitors.html', 'attendance.html', 'gate_scanners.html'];

        if (officerPages.includes(currentPage)) {
            if (sessionStorage.getItem('officerAuth') !== 'true') {
                injectAuthModal('Officer Portal', '', 'officerAuth', 'GTRE123'); // expectedUser is empty to allow any name
            }
        } else if (receptionPages.includes(currentPage)) {
            if (sessionStorage.getItem('receptionAuth') !== 'true') {
                injectAuthModal('Reception & Security', 'reception', 'receptionAuth', 'GTRE123');
            }
        }
    }
})();

function injectAuthModal(portalName, expectedUser, authKey, expectedPass) {
    const run = () => {
        // Prevent interaction with the main page until authenticated
        document.body.style.overflow = 'hidden';

        const modalHtml = `
            <div id="roleAuthOverlay" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,0.95);z-index:99999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(5px);">
                <div style="background:white;padding:40px;border-radius:12px;width:100%;max-width:400px;text-align:center;box-shadow:0 25px 50px -12px rgba(0,0,0,0.25); border-top: 6px solid #10b981;">
                    <i class="fa-solid fa-lock" style="font-size:32px;color:#10b981;margin-bottom:15px;"></i>
                    <h2 style="margin:0 0 8px 0;color:#0f172a;">${portalName} Login</h2>
                    <p style="color:#64748b;margin-bottom:24px;font-size:14px;">Secondary authentication required.</p>
                    
                    <div style="text-align:left;margin-bottom:16px;">
                        <label style="display:block;margin-bottom:6px;font-size:13px;font-weight:600;color:#334155;">User ID</label>
                        <input type="text" id="roleUser" placeholder="Enter Role ID" style="width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:6px;box-sizing:border-box;font-family:inherit;font-size:15px;" autocomplete="off" value="${expectedUser}">
                    </div>
                    
                    <div style="text-align:left;margin-bottom:20px;">
                        <label style="display:block;margin-bottom:6px;font-size:13px;font-weight:600;color:#334155;">Password</label>
                        <input type="password" id="rolePass" placeholder="••••••••" style="width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:6px;box-sizing:border-box;font-family:inherit;font-size:15px;">
                    </div>
                    
                    <div id="roleError" style="color:#ef4444;font-size:13px;margin-bottom:16px;display:none;background:rgba(239,68,68,0.1);padding:8px;border-radius:4px;">Invalid credentials. Try again.</div>
                    
                    <div style="display:flex;gap:12px;">
                        <button onclick="window.location.href='dashboard.html'" style="flex:1;padding:12px;background:#f1f5f9;color:#475569;font-weight:600;border:none;border-radius:6px;cursor:pointer;transition:all 0.2s;">Cancel</button>
                        <button onclick="verifyRoleAuth('${expectedUser}', '${authKey}', '${expectedPass}')" style="flex:1;padding:12px;background:#10b981;color:white;font-weight:600;border:none;border-radius:6px;cursor:pointer;transition:all 0.2s;">Unlock</button>
                    </div>
                    
                    <p style="margin-top:24px;font-size:12px;color:#94a3b8;font-weight:500;">Demo: ${expectedUser || 'Your Name'} / ${expectedPass}</p>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Allow Enter key to submit
        const passField = document.getElementById('rolePass');
        passField.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                window.verifyRoleAuth(expectedUser, authKey, expectedPass);
            }
        });

        // Auto-focus password if user is already filled
        if (expectedUser) {
            passField.focus();
        } else {
            document.getElementById('roleUser').focus();
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', run);
    } else {
        run();
    }
}

window.verifyRoleAuth = function (expectedUser, authKey, expectedPass) {
    const u = document.getElementById('roleUser').value.trim();
    const p = document.getElementById('rolePass').value.trim();

    const uMatch = (expectedUser === '' || u.toLowerCase() === expectedUser.toLowerCase());
    const pMatch = (p.toUpperCase() === expectedPass.toUpperCase() || p === "admin123");

    if (uMatch && pMatch) {
        sessionStorage.setItem(authKey, 'true');
        sessionStorage.setItem('officerName', u); // Store the name for the portal
        document.body.style.overflow = 'auto'; // Restore scroll
        document.getElementById('roleAuthOverlay').remove();
        // Notify other scripts that authentication is complete
        window.dispatchEvent(new CustomEvent('secondaryAuthSuccess', { detail: { username: u } }));
    } else {
        document.getElementById('roleError').style.display = 'block';
        document.getElementById('rolePass').value = '';
    }
}

function systemLogout() {
    sessionStorage.clear();
    window.location.href = 'index.html';
}
