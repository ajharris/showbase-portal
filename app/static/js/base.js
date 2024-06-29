document.addEventListener('DOMContentLoaded', (event) => {
    const viewCheckbox = document.getElementById('view-checkbox');
    const themeCheckbox = document.getElementById('theme-checkbox');
    const adminFields = document.querySelectorAll('.admin-field');
    const accountManagerFields = document.querySelectorAll('.account-manager-field');
    const adminDropdown = document.querySelector('.admin-dropdown');
    const accountManagerDropdown = document.querySelector('.account-manager-dropdown');

    if (themeCheckbox) {
        const currentTheme = localStorage.getItem('theme') || 'light';
        console.log(`Current theme: ${currentTheme}`); // Debug log
        document.body.classList.add(currentTheme + '-mode');
        document.querySelector('.navbar-inverse').classList.add(currentTheme + '-mode');
        themeCheckbox.checked = currentTheme === 'dark';

        themeCheckbox.addEventListener('change', function() {
            const newTheme = this.checked ? 'dark' : 'light';
            console.log(`Switching to ${newTheme} theme`); // Debug log
            document.body.classList.toggle('light-mode', newTheme === 'light');
            document.body.classList.toggle('dark-mode', newTheme === 'dark');
            document.querySelector('.navbar-inverse').classList.toggle('light-mode', newTheme === 'light');
            document.querySelector('.navbar-inverse').classList.toggle('dark-mode', newTheme === 'dark');
            localStorage.setItem('theme', newTheme);

            fetch("/save_theme", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({ theme: newTheme })
            });
        });
    }

    if (viewCheckbox) {
        function toggleFields() {
            if (viewCheckbox.checked) {
                adminFields.forEach(field => field.style.display = 'none');
                accountManagerFields.forEach(field => field.style.display = 'none');
                if (adminDropdown) adminDropdown.style.display = 'none';
                if (accountManagerDropdown) accountManagerDropdown.style.display = 'none';
            } else {
                adminFields.forEach(field => field.style.display = 'block');
                accountManagerFields.forEach(field => field.style.display = 'block');
                if (adminDropdown) adminDropdown.style.display = 'block';
                if (accountManagerDropdown) accountManagerDropdown.style.display = 'block';
            }
        }

        const viewAsEmployee = localStorage.getItem('viewAsEmployee') === 'true';
        viewCheckbox.checked = viewAsEmployee;
        toggleFields(); // Initial call to set the correct state

        viewCheckbox.addEventListener('change', function() {
            const viewMode = this.checked ? 'true' : 'false';
            localStorage.setItem('viewAsEmployee', viewMode);
            toggleFields();

            fetch("/save_view_mode", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({ viewAsEmployee: viewMode })
            }).then(() => {
                location.reload();
            });
        });
    }
});

function setEventStatus(eventId, status) {
    fetch(`/set_event_status/${eventId}/${status}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    }).then(response => {
        if (response.ok) {
            location.reload();
        } else {
            alert('Failed to update event status.');
        }
    });
}
