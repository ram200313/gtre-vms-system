// js/auth.js
(function () {
    const protectedPages = [
        'new_visitor.html',
        'todays_visitors.html',
        'attendance.html',
        'gate_scanners.html',
        'dashboard.html',
        'admin_dashboard.html' // Maybe not this one, it has its own auth?
    ];

    // We will apply this system-level auth check to all html files except index.html and admin_login.html
    const currentPagePath = window.location.pathname;
    const currentPage = currentPagePath.split('/').pop() || 'index.html';

    // If we're on a page other than index.html or admin_login.html
    if (currentPage !== 'index.html' && currentPage !== 'admin_login.html') {
        const token = sessionStorage.getItem('systemToken');
        if (!token) {
            // Not authenticated, redirect to system login
            window.location.href = 'index.html';
        }
    }
})();

function systemLogout() {
    sessionStorage.removeItem('systemToken');
    sessionStorage.removeItem('adminToken'); // Also clear admin token if logging out completely
    window.location.href = 'index.html';
}
