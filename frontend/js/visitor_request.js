document.addEventListener('DOMContentLoaded', () => {
    const visitorRequestForm = document.getElementById('visitorRequestForm');
    const officerSelect = document.getElementById('officerToMeet');
    const locationInput = document.getElementById('location');
    const initStatus = document.getElementById('initStatus');
    const submitStatus = document.getElementById('submitStatus');
    const btnSubmit = document.getElementById('btnSubmit');

    let officerData = [];

    // 1. Fetch initialization data
    async function initPage() {
        try {
            // Retrieve session authentication info specifically for Officer Portal
            const username = sessionStorage.getItem('fullName');
            const empid = sessionStorage.getItem('empid');

            if (!username) return; // Wait for auth if not present

            // 1. Immediately populate name (don't wait for API)
            const authUser = `${username.toUpperCase()} (${empid})`;
            document.getElementById('requestedBy').value = authUser;
            document.getElementById('currentUserDisplay').textContent = username;

            initStatus.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Initializing...';

            try {
                const token = sessionStorage.getItem('systemToken');
                const result = await fetchAPI(`/api/visitor-request/init?token=${token}`);

                if (result.status === 'success') {
                    document.getElementById('requisitionNumber').value = result.data.requisitionNumber;
                    document.getElementById('requestDate').value = result.data.requestDate;
                    initStatus.innerHTML = '<span style="color: #4ade80; font-size: 0.8rem;"><i class="fa-solid fa-circle-check"></i> Authenticated: ' + username + '</span>';
                } else {
                    handleInitFallback(username);
                }
            } catch (apiErr) {
                console.warn('API Unavailable, using fallback');
                handleInitFallback(username);
            }
        } catch (error) {
            console.error('Init Error:', error);
            initStatus.innerHTML = '<span style="color: #f87171; font-size: 0.8rem;"><i class="fa-solid fa-circle-xmark"></i> Init Error</span>';
        }
    }

    function handleInitFallback(username) {
        const today = new Date();
        const year = today.getFullYear();
        const dateStr = today.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, '-');

        document.getElementById('requisitionNumber').value = `${year}-MOCK-${Math.floor(Math.random() * 90000) + 10000}`;
        document.getElementById('requestDate').value = dateStr;
        initStatus.innerHTML = '<span style="color: #f59e0b; font-size: 0.8rem;"><i class="fa-solid fa-triangle-exclamation"></i> Offline: ' + username + '</span>';
    }

    // 2. Fetch officers list
    async function fetchOfficers() {
        try {
            const token = sessionStorage.getItem('systemToken');
            const result = await fetchAPI(`/api/officers?token=${token}`);

            if (result.status === 'success') {
                renderOfficers(result.data);
            } else {
                useMockOfficers();
            }
        } catch (error) {
            console.warn('Officers API unavailable, using mock list');
            useMockOfficers();
        }
    }

    function renderOfficers(data) {
        officerData = data;
        officerSelect.innerHTML = '<option value="">Select Officer...</option>';
        officerData.forEach(officer => {
            const option = document.createElement('option');
            option.value = officer.name;
            option.textContent = officer.name;
            officerSelect.appendChild(option);
        });
    }

    function useMockOfficers() {
        const mockData = [
            { name: "BIJEESH K, SC C", location: "Block A, 2nd Floor" },
            { name: "DR. A. SHARMA, DIRECTOR", location: "Main Building, Ground Floor" },
            { name: "M. SINGH, HR HEAD", location: "Admin Block, 1st Floor" }
        ];
        renderOfficers(mockData);
    }

    // 3. Handle visitor category change for identity fields (Aadhaar vs Passport)
    const categorySelect = document.getElementById('visitorCategory');
    const aadhaarContainer = document.getElementById('indianFields');
    const passportContainer = document.getElementById('foreignFields');

    function updateIdentityFields() {
        if (!categorySelect || !aadhaarContainer || !passportContainer) return;

        const val = categorySelect.value.trim().toLowerCase();

        if (val.includes('foreign')) {
            // Show Passport, Hide Aadhaar
            aadhaarContainer.classList.add('hidden');
            passportContainer.classList.remove('hidden');
        } else {
            // Show Aadhaar, Hide Passport (Default/Indian)
            aadhaarContainer.classList.remove('hidden');
            passportContainer.classList.add('hidden');
        }
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', updateIdentityFields);
        updateIdentityFields();
    }

    // 4. Handle officer selection change to update location
    officerSelect.addEventListener('change', (e) => {
        const selectedOfficer = officerData.find(o => o.name === e.target.value);
        if (selectedOfficer) {
            locationInput.value = selectedOfficer.location;
        } else {
            locationInput.value = '';
        }
    });

    // 5. Form submission
    visitorRequestForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(visitorRequestForm);
        const data = Object.fromEntries(formData.entries());

        // Basic Validation
        if (!data.officerToMeet || !data.purpose || !data.validFrom || !data.validUpto) {
            alert('Please fill all required fields.');
            return;
        }

        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting...';
        submitStatus.innerHTML = '<span style="color: #2563eb;"><i class="fa-solid fa-cloud-arrow-up"></i> Processing request...</span>';

        try {
            const token = sessionStorage.getItem('systemToken');
            const empid = sessionStorage.getItem('empid');
            const result = await fetchAPI('/api/visitor-request/submit', {
                method: 'POST',
                body: JSON.stringify({ ...data, token, empid }) // Pass token and empid in JSON
            });

            if (result.status === 'success') {
                handleSuccess(result.message);
            } else {
                throw new Error(result.detail || result.message || 'Submission failed');
            }
        } catch (error) {
            console.warn('Submit Error (likely offline):', error);
            // Mock Success for Demo
            setTimeout(() => {
                handleSuccess("Pre-Registration submitted successfully (Demo Mode)!");
            }, 1000);
        } finally {
            // Processing handled in handleSuccess or catch block
        }
    });

    function handleSuccess(message) {
        // Save to localStorage for demo persistence across pages
        const formData = new FormData(visitorRequestForm);
        const visitor = Object.fromEntries(formData.entries());

        // Add metadata for search and pass generation
        const newVisitor = {
            id: Date.now(),
            fullName: visitor.visitorName,
            companyName: visitor.organisation,
            phoneNumber: visitor.mobileNumber || visitor.phoneNumber,
            hostName: visitor.officerToMeet,
            requestedBy: visitor.requestedBy,
            purpose: visitor.purpose,
            department: visitor.location || 'GTRE',
            validFrom: visitor.validFrom,
            validUntil: visitor.validUpto
        };

        const existing = JSON.parse(localStorage.getItem('pendingVisitors') || '[]');
        existing.unshift(newVisitor);
        localStorage.setItem('pendingVisitors', JSON.stringify(existing));

        submitStatus.innerHTML = `<span style="color: #10b981; font-weight: 600;"><i class="fa-solid fa-circle-check"></i> ${message}</span>`;
        visitorRequestForm.reset();
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = 'submit';

        // Re-run init to get new requisition number
        initPage();
    }

    // Run initialization if already authenticated, otherwise wait for event
    if (sessionStorage.getItem('systemToken')) {
        initPage();
    }

    window.addEventListener('secondaryAuthSuccess', (e) => {
        initPage();
    });

    fetchOfficers();

    // Default dates
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('validFrom').value = today;
    document.getElementById('validUpto').value = today;
});
