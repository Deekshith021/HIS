/*
 * his/static/his/js/login.js
 * JavaScript for the HIS login page.
 */

document.addEventListener('DOMContentLoaded', () => {
    const passwordInput = document.getElementById('id_password');
    const togglePasswordIcon = document.getElementById('togglePassword');

    if (togglePasswordIcon) {
        togglePasswordIcon.addEventListener('click', function() {
            // Toggle the type attribute
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);

            // Toggle the icon
            this.classList.toggle('fa-eye');
            this.classList.toggle('fa-eye-slash');
        });
    }
});
