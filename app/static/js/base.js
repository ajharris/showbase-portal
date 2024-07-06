document.addEventListener('DOMContentLoaded', (event) => {
    const viewCheckbox = document.getElementById('view-checkbox');
    const themeCheckbox = document.getElementById('theme-checkbox');
    const viewCheckboxManager = document.getElementById('view-checkbox-manager');
    const adminFields = document.querySelectorAll('.admin-field');
    const accountManagerFields = document.querySelectorAll('.account-manager-field');
    const adminDropdown = document.querySelector('.admin-dropdown');
    const accountManagerDropdown = document.querySelector('.account-manager-dropdown');

    // Theme toggle functionality
    if (themeCheckbox) {
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.body.classList.add(currentTheme + '-mode');
        document.querySelector('.navbar-inverse').classList.add(currentTheme + '-mode');
        themeCheckbox.checked = currentTheme === 'dark';

        themeCheckbox.addEventListener('change', function() {
            const newTheme = this.checked ? 'dark' : 'light';
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
            }).catch(error => console.error('Error:', error));
        });
    }

    // Function to toggle view as employee fields
    function toggleFields() {
        if (viewCheckbox && viewCheckbox.checked) {
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

    // Function to toggle view as manager fields
    function toggleManagerFields() {
        if (viewCheckboxManager && viewCheckboxManager.checked) {
            adminFields.forEach(field => field.style.display = 'none');
            if (adminDropdown) adminDropdown.style.display = 'none';
        } else {
            adminFields.forEach(field => field.style.display = 'block');
            if (adminDropdown) adminDropdown.style.display = 'block';
        }
    }

    // View as Employee functionality
    if (viewCheckbox) {
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
                body: JSON.stringify({ viewAsEmployee: viewMode, viewAsManager: 'false' })
            }).then(() => {
                location.reload();
            }).catch(error => console.error('Error:', error));
        });
    }

    // View as Account Manager functionality
    if (viewCheckboxManager) {
        const viewAsManager = localStorage.getItem('viewAsManager') === 'true';
        viewCheckboxManager.checked = viewAsManager;
        toggleManagerFields(); // Initial call to set the correct state

        viewCheckboxManager.addEventListener('change', function() {
            const viewMode = this.checked ? 'true' : 'false';
            localStorage.setItem('viewAsManager', viewMode);
            toggleManagerFields();

            fetch("/save_view_mode", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({ viewAsManager: viewMode, viewAsEmployee: 'false' })
            }).then(() => {
                location.reload();
            }).catch(error => console.error('Error:', error));
        });
    }

    // Initialize flatpickr
    flatpickr(".datetimepicker", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
    });

    // Worker select functionality
    const workerSelect = document.getElementById('worker_select');
    if (workerSelect) {
        workerSelect.addEventListener('change', function() {
            const selectedWorkerId = workerSelect.value;
            if (selectedWorkerId) {
                const url = workerSelect.getAttribute('data-url');
                if (url) {
                    window.location.href = url + "?worker_id=" + selectedWorkerId;
                } else {
                    console.error('Data-url attribute not found.');
                }
            }
        });
    }
});

// Function to set event status
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
    }).catch(error => console.error('Error:', error));
}

// Initialize Flatpickr for date-time pickers
document.addEventListener('DOMContentLoaded', function () {
    flatpickr('#shift_start', {
        enableTime: true,
        dateFormat: 'm/d/Y h:i K'
    });

    flatpickr('#shift_end', {
        enableTime: true,
        dateFormat: 'm/d/Y h:i K'
    });
});

// Confirm Delete Function
function confirmDelete(eventId) {
    if (confirm("Are you sure you want to delete this event? This action cannot be undone.")) {
        document.getElementById('delete-event-form-' + eventId).submit();
    }
}
