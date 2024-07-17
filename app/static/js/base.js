document.addEventListener('DOMContentLoaded', (event) => {
    const viewCheckbox = document.getElementById('view-checkbox');
    const themeCheckbox = document.getElementById('theme-checkbox');
    const viewCheckboxManager = document.getElementById('view-checkbox-manager');
    const adminFields = document.querySelectorAll('.admin-field');
    const accountManagerFields = document.querySelectorAll('.account-manager-field');
    const adminDropdown = document.querySelector('.admin-dropdown');
    const accountManagerDropdown = document.querySelector('.account-manager-dropdown');

    // Function to toggle fields based on mode
    function toggleFields(viewAsEmployee, viewAsManager) {
        const toggleVisibility = (elements, isVisible) => {
            elements.forEach(field => field.style.display = isVisible ? 'block' : 'none');
        };

        console.log('View as Employee:', viewAsEmployee);
        console.log('View as Manager:', viewAsManager);

        toggleVisibility(adminFields, !viewAsEmployee && !viewAsManager);
        toggleVisibility(accountManagerFields, !viewAsEmployee);
        if (adminDropdown) adminDropdown.style.display = viewAsEmployee || viewAsManager ? 'none' : 'block';
        if (accountManagerDropdown) accountManagerDropdown.style.display = viewAsEmployee ? 'none' : 'block';
    }

    // Theme toggle functionality
    if (themeCheckbox) {
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.body.classList.add(`${currentTheme}-mode`);
        document.querySelector('.navbar-inverse').classList.add(`${currentTheme}-mode`);
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

    // Function to handle checkbox change
    function handleCheckboxChange(checkbox, key, callback) {
        const viewMode = checkbox.checked ? 'true' : 'false';
        if (viewMode !== localStorage.getItem(key)) {
            localStorage.setItem(key, viewMode);

            fetch("/save_view_mode", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({ [key]: viewMode })
            }).then(() => {
                location.reload();
            }).catch(error => console.error('Error:', error));
        }
    }

    // View as Employee functionality
    if (viewCheckbox) {
        const viewAsEmployee = localStorage.getItem('viewAsEmployee') === 'true';
        viewCheckbox.checked = viewAsEmployee;
        toggleFields(viewAsEmployee, false);

        viewCheckbox.addEventListener('change', function() {
            handleCheckboxChange(viewCheckbox, 'viewAsEmployee', toggleFields);
        });
    }

    // View as Account Manager functionality
    if (viewCheckboxManager) {
        const viewAsManager = localStorage.getItem('viewAsManager') === 'true';
        viewCheckboxManager.checked = viewAsManager;
        toggleFields(false, viewAsManager);

        viewCheckboxManager.addEventListener('change', function() {
            handleCheckboxChange(viewCheckboxManager, 'viewAsManager', toggleFields);
        });
    }

    // Initial state handling
    const viewAsEmployee = localStorage.getItem('viewAsEmployee') === 'true';
    const viewAsManager = localStorage.getItem('viewAsManager') === 'true';
    toggleFields(viewAsEmployee, viewAsManager);

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

    // Form submission validation for forms that require crew ID
    document.querySelectorAll('form.requires-crew-id').forEach(form => {
        form.addEventListener('submit', (e) => {
            const formData = new FormData(form);
            const crewId = formData.get('crew_id');
            if (!crewId || crewId === '') {
                alert('Crew ID is missing!');
                e.preventDefault();
            }
        });
    });
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
