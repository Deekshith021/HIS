document.addEventListener('DOMContentLoaded', () => {
    // Select the theme toggle button and the body element
    const themeToggleButton = document.getElementById('theme-toggle');
    const body = document.body;

    // --- 1. Check for a saved theme in localStorage and apply it on page load ---
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-theme');
    }

    // --- 2. Add a click event listener to the toggle button ---
    themeToggleButton.addEventListener('click', () => {
        // Toggle the .dark-theme class on the body
        body.classList.toggle('dark-theme');

        // --- 3. Save the user's preference to localStorage ---
        if (body.classList.contains('dark-theme')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });
});