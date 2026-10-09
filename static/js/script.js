/**
 * AI Production Planner - Interactive JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle AI Generation Form submission with animated loader
    const plannerForms = document.querySelectorAll('.ai-generate-form');
    const loaderOverlay = document.getElementById('aiLoaderOverlay');

    plannerForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            if (loaderOverlay) {
                loaderOverlay.style.display = 'flex';
            }
        });
    });

    // Print schedule helper
    const printBtn = document.getElementById('printScheduleBtn');
    if (printBtn) {
        printBtn.addEventListener('click', function () {
            window.print();
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 6000);
    });
});

function showAILoader() {
    const loader = document.getElementById('aiLoaderOverlay');
    if (loader) {
        loader.style.display = 'flex';
    }
}
