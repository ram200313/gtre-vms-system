document.addEventListener('DOMContentLoaded', () => {

    // Set default dates for datetime-local
    const setDateDefaults = () => {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        const todayTime = now.toISOString().slice(0, 16);
        document.getElementById('validFromDate').value = todayTime;

        const endOfDay = new Date(now);
        endOfDay.setHours(18, 0, 0, 0);
        if (now.getTime() > endOfDay.getTime()) {
            endOfDay.setDate(endOfDay.getDate() + 1);
        }
        document.getElementById('validUntilDate').value = endOfDay.toISOString().slice(0, 16);
    };
    setDateDefaults();



    // Dynamic Nationality Logic
    const nationalitySelect = document.getElementById('nationality');
    const indianFields = document.getElementById('indianFields');
    const foreignFields = document.getElementById('foreignFields');

    nationalitySelect.addEventListener('change', (e) => {
        if (e.target.value === 'Indian') {
            indianFields.classList.add('active');
            foreignFields.classList.remove('active');
            document.getElementById('aadhaarNumber').required = true;
            document.getElementById('passportNumber').required = false;
        } else {
            indianFields.classList.remove('active');
            foreignFields.classList.add('active');
            document.getElementById('aadhaarNumber').required = false;
            document.getElementById('passportNumber').required = true;
            document.getElementById('countryDropdown').required = true;
        }
    });

    // Device Deposit Logic
    const phoneDepositedCb = document.getElementById('phoneDeposited');
    const lockerSelectionBox = document.getElementById('lockerSelection');

    phoneDepositedCb.addEventListener('change', (e) => {
        if (e.target.checked) {
            lockerSelectionBox.classList.remove('hidden');
            document.getElementById('lockerNumber').required = true;
        } else {
            lockerSelectionBox.classList.add('hidden');
            document.getElementById('lockerNumber').required = false;
            document.getElementById('lockerNumber').value = "";
        }
    });

    // Form submission handling
    document.getElementById('visitorRegistrationForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        // Custom validations
        const nationality = document.getElementById('nationality').value;
        if (nationality === 'Indian') {
            const aadhaar = document.getElementById('aadhaarNumber').value;
            if (aadhaar && (aadhaar.length !== 12 || !/^\d+$/.test(aadhaar))) {
                alert("Aadhaar Number must be exactly 12 digits.");
                return;
            }
        }

        const phone = document.getElementById('phoneNumber').value;
        if (phone.length !== 10 || !/^\d+$/.test(phone)) {
            alert("Phone Number must be exactly 10 digits.");
            return;
        }

        const allowedBlocks = document.getElementById('allowedBlocks');
        if (allowedBlocks.selectedOptions.length === 0) {
            alert("Select at least one allowed block.");
            return;
        }

        const blocksArray = Array.from(allowedBlocks.selectedOptions).map(opt => opt.value);

        // Build Form Data
        const formData = new FormData(e.target);
        formData.append('allowedBlocks', JSON.stringify(blocksArray));

        const submitBtn = document.getElementById('btnSave');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

        const submitStatus = document.getElementById('submitStatus');
        submitStatus.className = 'submit-status processing';
        submitStatus.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Saving Pre-Registration Data Offline...';

        try {
            const response = await fetch('/api/visitors/officer_register', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok && (result.status === 'success' || result.status === 'warning')) {
                submitStatus.className = 'submit-status success';
                submitStatus.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${result.message}`;
                e.target.reset();
                setDateDefaults(); // Reset dates
            } else {
                throw new Error(result.detail || result.message || "Failed to save record.");
            }
        } catch (error) {
            submitStatus.className = 'submit-status error';
            submitStatus.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> System Error: ${error.message}`;
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });
});
