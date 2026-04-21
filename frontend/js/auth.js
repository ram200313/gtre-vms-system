// Initialize API_BASE_URL dynamically to support both local testing and Cloud (Render) Deployment
const API_BASE_URL = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' || window.location.protocol === 'file:') 
    ? 'http://127.0.0.1:8000' 
    : '';

/**
 * Global helper to fetch from the backend API, handle port mismatch,
 * and provide consistent error handling.
 */
window.fetchAPI = async function (endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

    // Default headers
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    try {
        const response = await fetch(url, { ...options, headers });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (err) {
        console.error(`API Fetch Error (${endpoint}):`, err);
        throw err;
    }
};

(function () {
    const currentPagePath = window.location.pathname;
    const currentPage = currentPagePath.split('/').pop() || 'index.html';

    // Dynamic Sidebar & Route Protection
    function checkAccess(role, page) {
        if (!role || role === 'admin') return true;
        try {
            const screensStr = sessionStorage.getItem('allowedScreens');
            if (screensStr) {
                 const allowedPages = JSON.parse(screensStr);
                 return allowedPages.includes(page);
            }
        } catch(e) {}
        return false;
    }

    function renderSidebar(role) {
        if (!role || role === 'admin') return;
        try {
            const screensStr = sessionStorage.getItem('allowedScreens');
            if (!screensStr) return;
            const allowedPages = JSON.parse(screensStr);
            
            // Map items to their target HTMLs
            const navMapping = {
                'nav-admin': 'admin_dashboard.html',
                'nav-dashboard': 'dashboard.html',
                'nav-pre-reg': 'visitor_request.html',
                'nav-my-visitors': 'officer_visitors.html',
                'nav-reception-dash': 'reception_dashboard.html',
                'nav-todays-visitors': 'todays_visitors.html',
                'nav-attendance': 'attendance.html',
                'nav-gate-scanners': 'gate_scanners.html'
            };
            
            for (const [id, page] of Object.entries(navMapping)) {
                const el = document.getElementById(id);
                if (el && !allowedPages.includes(page)) {
                    el.style.display = 'none';
                }
            }
            
            // Hide Category Labels if children are hidden
            const officerItemsVisible = document.getElementById('nav-pre-reg')?.style.display !== 'none' || document.getElementById('nav-my-visitors')?.style.display !== 'none';
            if (!officerItemsVisible) {
                const l1 = document.getElementById('label-officer');
                if (l1) l1.style.display = 'none';
            }
            
            const reqItemsVisible = document.getElementById('nav-reception-dash')?.style.display !== 'none' || document.getElementById('nav-todays-visitors')?.style.display !== 'none';
            if (!reqItemsVisible) {
                const l2 = document.getElementById('label-reception');
                if (l2) l2.style.display = 'none';
            }
        } catch(e) { console.error('Sidebar error', e); }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const token = sessionStorage.getItem('systemToken');
        const role = sessionStorage.getItem('systemRole');

        if (currentPage !== 'index.html' && currentPage !== 'admin_login.html' && currentPage !== 'unauthorized.html') {
            if (!token) {
                window.location.href = 'index.html';
                return;
            }

            // Route Protection
            if (!checkAccess(role, currentPage)) {
                window.location.href = 'unauthorized.html';
                return;
            }
        }

        // Apply Sidebar Filtering
        renderSidebar(role);

        // Update Header
        const fullNameStr = sessionStorage.getItem('fullName');
        const name = fullNameStr || (role === 'admin' ? 'Administrator' : (role ? role.toUpperCase() : 'User'));

        document.querySelectorAll('.user-name').forEach(el => {
            el.textContent = name;
        });
        document.querySelectorAll('.user-role').forEach(el => {
            el.textContent = role ? role.toUpperCase() : 'System User';
        });

        const avatar = document.querySelector('.avatar');
        if (avatar && name) {
            avatar.textContent = name.substring(0, 2).toUpperCase();
        }
    });
})();

function injectAuthModal(portalName, expectedUser, authKey, expectedPass) {
    // Secondary auth modals are no longer used; authentication is robust at login.
    console.log("Mock secondary auth skipped for:", portalName);
}

window.verifyRoleAuth = function() {};

function systemLogout() {
    sessionStorage.clear();
    window.location.href = 'index.html';
}
