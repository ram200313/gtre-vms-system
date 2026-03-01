document.addEventListener('DOMContentLoaded', () => {

    // Set default dates
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('visitDate').value = today;

    // Fetch Scheduled Visitors (Pre-filled by Host)
    const scheduledVisitorSelect = document.getElementById('scheduledVisitor');
    let scheduledData = [];

    if (scheduledVisitorSelect) {
        fetch('/api/visitors/scheduled')
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    scheduledData = data.data;
                    scheduledData.forEach(v => {
                        const option = document.createElement('option');
                        option.value = v.id;
                        option.textContent = `${v.fullName} (Host: ${v.hostName})`;
                        scheduledVisitorSelect.appendChild(option);
                    });
                }
            })
            .catch(err => console.error("Error fetching scheduled visitors for pre-registration:", err));

        scheduledVisitorSelect.addEventListener('change', (e) => {
            const selectedId = e.target.value;
            if (selectedId) {
                const visitor = scheduledData.find(v => v.id === selectedId);
                if (visitor) {
                    // Pre-fill fields!
                    document.getElementById('fullName').value = visitor.fullName;
                    document.getElementById('phoneNumber').value = visitor.phoneNumber;

                    // Optional extra fields set by host
                    if (visitor.purposeOfVisit) document.getElementById('purposeOfVisit').value = visitor.purposeOfVisit;

                    // Match Host Dropdown intelligently
                    if (visitor.hostName) {
                        const hostDropdown = document.getElementById('hostName');
                        for (let i = 0; i < hostDropdown.options.length; i++) {
                            if (hostDropdown.options[i].text.includes(visitor.hostName) ||
                                visitor.hostName.includes(hostDropdown.options[i].value)) {
                                hostDropdown.selectedIndex = i;
                                break;
                            }
                        }
                    }
                }
            } else {
                // Clear fields if unchecked
                document.getElementById('fullName').value = "";
                document.getElementById('phoneNumber').value = "";
                document.getElementById('purposeOfVisit').value = "";
                document.getElementById('hostName').value = "";
            }
        });
    }

    // Dynamic Nationality Logic
    const nationalitySelect = document.getElementById('nationality');
    const indianFields = document.getElementById('indianFields');
    const foreignFields = document.getElementById('foreignFields');

    nationalitySelect.addEventListener('change', (e) => {
        if (e.target.value === 'Indian') {
            indianFields.classList.add('active');
            foreignFields.classList.remove('active');

            // Set required attributes
            document.getElementById('aadhaarNumber').required = true;
            document.getElementById('passportNumber').required = false;
        } else {
            indianFields.classList.remove('active');
            foreignFields.classList.add('active');

            // Set required attributes
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

    // Offline Webcam Handling
    const webcamPreview = document.getElementById('webcamPreview');
    const photoCanvas = document.getElementById('photoCanvas');
    const capturedPhoto = document.getElementById('capturedPhoto');
    const photoBase64Input = document.getElementById('photoBase64');

    const startCamBtn = document.getElementById('startCamBtn');
    const takePhotoBtn = document.getElementById('takePhotoBtn');
    const retakePhotoBtn = document.getElementById('retakePhotoBtn');
    const cameraStatus = document.getElementById('cameraStatus');

    let stream = null;

    async function startCamera() {
        try {
            cameraStatus.textContent = "Requesting camera access...";
            cameraStatus.className = "status-message info";

            // Request offline camera capabilities (no internet needed)
            stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: "user" }
            });

            webcamPreview.srcObject = stream;
            webcamPreview.style.display = 'block';
            capturedPhoto.style.display = 'none';

            takePhotoBtn.disabled = false;
            startCamBtn.disabled = true;
            retakePhotoBtn.classList.add('hidden');

            photoBase64Input.value = ""; // Clear existing

            cameraStatus.textContent = "Camera active. Position face and capture.";
            cameraStatus.className = "status-message success";
            cameraStatus.style.backgroundColor = "#D1FAE5";
            cameraStatus.style.color = "#065F46";

        } catch (err) {
            console.error("Camera access error:", err);
            cameraStatus.textContent = "Error: Camera access denied or device not found.";
            cameraStatus.className = "status-message error";
            cameraStatus.style.backgroundColor = "#FEE2E2";
            cameraStatus.style.color = "#991B1B";
        }
    }

    function takePhoto() {
        if (!stream) return;

        // Match canvas dimensions to video feed
        photoCanvas.width = webcamPreview.videoWidth;
        photoCanvas.height = webcamPreview.videoHeight;

        // Draw video frame to canvas
        const context = photoCanvas.getContext('2d');
        context.drawImage(webcamPreview, 0, 0, photoCanvas.width, photoCanvas.height);

        // Convert to Base64 (Local in-memory processing)
        const photoDataUrl = photoCanvas.toDataURL('image/jpeg', 0.85);

        // Show frozen captured frame
        capturedPhoto.src = photoDataUrl;
        capturedPhoto.style.display = 'block';

        // Save base64 to hidden form input for submission
        photoBase64Input.value = photoDataUrl;

        // UI Updates
        takePhotoBtn.disabled = true;
        retakePhotoBtn.classList.remove('hidden');
        cameraStatus.textContent = "Photo captured successfully for local storage.";

        // Stop camera stream to free resources until retake/submit
        stopCamera();
    }

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        startCamBtn.disabled = false;
    }

    function retakePhoto() {
        capturedPhoto.style.display = 'none';
        photoBase64Input.value = "";
        startCamera();
    }

    startCamBtn.addEventListener('click', startCamera);
    takePhotoBtn.addEventListener('click', takePhoto);
    retakePhotoBtn.addEventListener('click', retakePhoto);

});

// Global form submission
async function submitForm(actionStatus) {
    const form = document.getElementById('visitorRegistrationForm');

    // Check HTML5 Validations
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    // Ensure photo is taken
    const base64Data = document.getElementById('photoBase64').value;
    if (!base64Data) {
        alert("Please Capture Visitor Photo before submitting.");
        return;
    }

    // Validate Aadhaar if Indian
    const nationality = document.getElementById('nationality').value;
    if (nationality === 'Indian') {
        const aadhaar = document.getElementById('aadhaarNumber').value;
        if (aadhaar.length !== 12 || !/^\d+$/.test(aadhaar)) {
            alert("Aadhaar Number must be exactly 12 digits.");
            return;
        }
    }

    // Validate phone
    const phone = document.getElementById('phoneNumber').value;
    if (phone.length !== 10 || !/^\d+$/.test(phone)) {
        alert("Phone Number must be exactly 10 digits.");
        return;
    }

    // Block selection check
    const allowedBlocks = document.getElementById('allowedBlocks');
    if (allowedBlocks.selectedOptions.length === 0) {
        alert("Select at least one allowed block.");
        return;
    }

    // Convert multiple select to JSON string array parameter
    const blocksArray = Array.from(allowedBlocks.selectedOptions).map(opt => opt.value);

    // Build Form Data
    const formData = new FormData(form);
    formData.append('allowedBlocks', JSON.stringify(blocksArray));
    formData.append('actionStatus', actionStatus);

    // Disable buttons
    const buttons = document.querySelectorAll('.action-buttons button');
    buttons.forEach(b => b.disabled = true);

    const submitStatus = document.getElementById('submitStatus');
    submitStatus.textContent = "Saving to Database...";
    submitStatus.className = "submit-status success"; // Temporarily use success color as processing state

    try {
        // Send to FastAPI Backend
        const response = await fetch('/api/visitors/register', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            if (result.status === 'success' || result.status === 'warning') {
                submitStatus.textContent = result.message;
                submitStatus.className = "submit-status success";

                setTimeout(() => {
                    clearForm();
                }, 3000);
            } else if (result.status === 'error') {
                submitStatus.textContent = result.message;
                submitStatus.className = "submit-status error";
            }
        } else {
            submitStatus.textContent = "Error: " + (result.detail || "Server error occurred");
            submitStatus.className = "submit-status error";
        }

    } catch (err) {
        console.error("Submission Error:", err);
        submitStatus.textContent = "Network Error: Could not connect to internal server. Ensure backend is running.";
        submitStatus.className = "submit-status error";
    } finally {
        // Re-enable buttons
        buttons.forEach(b => b.disabled = false);
    }
}

function clearForm() {
    document.getElementById('visitorRegistrationForm').reset();

    // Reset defaults
    document.getElementById('visitDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('photoBase64').value = "";

    // Reset displays
    document.getElementById('capturedPhoto').style.display = 'none';
    document.getElementById('indianFields').classList.add('active');
    document.getElementById('foreignFields').classList.remove('active');
    document.getElementById('lockerSelection').classList.add('hidden');

    document.getElementById('submitStatus').className = "submit-status";
    document.getElementById('submitStatus').textContent = "";

    document.getElementById('takePhotoBtn').disabled = true;
    document.getElementById('startCamBtn').disabled = false;
    document.getElementById('retakePhotoBtn').classList.add('hidden');
    document.getElementById('cameraStatus').textContent = "Camera is inactive. Click 'Start Camera' to begin.";
    document.getElementById('cameraStatus').className = "status-message info";

    // Make sure we stop the stream if it's active
    const startCamBtn = document.getElementById('startCamBtn');
    startCamBtn.click(); // Hacky but works for resetting stream, or could explicitly call stopCamera()
}
