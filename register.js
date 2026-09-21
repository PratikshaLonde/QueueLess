const API_URL = window.location.origin;

const registerForm = document.getElementById("registerForm");
const messageBox = document.getElementById("message");
const registerBtn = document.getElementById("registerBtn");

function showMessage(message, type) {
    messageBox.textContent = message;
    messageBox.className = "message " + type;
}

registerForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const fullName = document.getElementById("fullName").value.trim();
    const collegeId = document.getElementById("collegeId").value.trim();
    const collegeName = document.getElementById("collegeName").value.trim();
    const collegeLocation = document.getElementById("collegeLocation").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    if (!fullName || !collegeId || !collegeName || !collegeLocation || !password) {
        showMessage("Please fill in all fields.", "error");
        return;
    }

    if (password.length < 4) {
        showMessage("Password must contain at least 4 characters.", "error");
        return;
    }

    if (password !== confirmPassword) {
        showMessage("Passwords do not match.", "error");
        return;
    }

    registerBtn.disabled = true;
    registerBtn.textContent = "Creating Account...";

    try {

        const response = await fetch(`${API_URL}/api/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                full_name: fullName,
                college_id: collegeId,
                college_name: collegeName,
                college_location: collegeLocation,
                password: password
            })
        });

        let data;

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {

            const errorMessage =
                data.message ||
                data.error ||
                "Registration failed. Please try again.";

            showMessage(errorMessage, "error");

            registerBtn.disabled = false;
            registerBtn.textContent = "Create Student Account";

            return;
        }

        showMessage(
            data.message || "Registration successful! You can now login.",
            "success"
        );

        registerForm.reset();

        setTimeout(() => {
            window.location.href = "student-login.html";
        }, 1500);

    } catch (error) {

        console.error("Registration error:", error);

        showMessage(
            "Cannot connect to QueueLess server. Make sure the Flask backend is running.",
            "error"
        );

        registerBtn.disabled = false;
        registerBtn.textContent = "Create Student Account";
    }
});