/**
 * Main JavaScript file for AYA Vision Detection Demo
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        
        // Stagger the animations
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * index);
    });

    // Initialize toasts
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    toastElList.map(function(toastEl) {
        return new bootstrap.Toast(toastEl);
    });

    // Handle image deletion
    setupImageDeletion();

    // Handle image modal
    setupImageModal();

    // Handle filtering and sorting
    setupFilteringAndSorting();
});

/**
 * Sets up image deletion functionality
 */
function setupImageDeletion() {
    // Get all delete buttons
    const deleteButtons = document.querySelectorAll('.delete-btn');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const imageId = this.dataset.id;
            const card = document.querySelector(`.result-card[data-id="${imageId}"]`);
            
            // Confirm deletion
            if (confirm('Are you sure you want to delete this image?')) {
                // Add removing animation class
                card.classList.add('removing');
                
                // Send delete request
                fetch(`/api/delete_image/${imageId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    }
                    throw new Error('Network response was not ok');
                })
                .then(data => {
                    // Remove card after animation completes
                    setTimeout(() => {
                        card.remove();
                        
                        // Show success toast
                        const toastContainer = document.querySelector('.toast-container');
                        if (toastContainer) {
                            const toast = document.createElement('div');
                            toast.className = 'toast';
                            toast.setAttribute('role', 'alert');
                            toast.setAttribute('aria-live', 'assertive');
                            toast.setAttribute('aria-atomic', 'true');
                            toast.innerHTML = `
                                <div class="toast-header">
                                    <strong class="me-auto">Success</strong>
                                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                                </div>
                                <div class="toast-body">
                                    Image deleted successfully.
                                </div>
                            `;
                            toastContainer.appendChild(toast);
                            const bsToast = new bootstrap.Toast(toast);
                            bsToast.show();
                            
                            // Remove toast after it's hidden
                            toast.addEventListener('hidden.bs.toast', function() {
                                toast.remove();
                            });
                        }
                        
                        // Update counts
                        updateCounts();
                    }, 300);
                })
                .catch(error => {
                    console.error('Error:', error);
                    card.classList.remove('removing');
                    alert('Failed to delete image. Please try again.');
                });
            }
        });
    });
}

/**
 * Sets up image modal functionality
 */
function setupImageModal() {
    // Get all result cards
    const resultCards = document.querySelectorAll('.result-card');
    
    resultCards.forEach(card => {
        card.addEventListener('click', function() {
            const imageId = this.dataset.id;
            const imageSrc = this.dataset.src;
            const filename = this.dataset.filename;
            const detectionResult = this.dataset.result;
            const subject = this.dataset.subject;
            
            // Get the modal
            const modal = document.getElementById('imageModal');
            const modalImage = modal.querySelector('.modal-image');
            const modalFilename = modal.querySelector('.modal-filename');
            const modalStatus = modal.querySelector('.modal-status');
            const modalDeleteBtn = modal.querySelector('.modal-delete-btn');
            
            // Set modal content
            modalImage.src = imageSrc;
            modalFilename.textContent = filename;
            
            // Set detection status with appropriate icon
            let statusHtml = '';
            if (detectionResult === 'true') {
                statusHtml = `<i class="fas fa-check-circle text-success"></i>${subject} Detected: Yes`;
            } else if (detectionResult === 'false') {
                statusHtml = `<i class="fas fa-times-circle text-danger"></i>${subject} Detected: No`;
            } else {
                statusHtml = `<i class="fas fa-question-circle text-secondary"></i>${subject} Detected: Unknown`;
            }
            modalStatus.innerHTML = statusHtml;
            
            // Set delete button data
            modalDeleteBtn.dataset.id = imageId;
            
            // Show the modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        });
    });
    
    // Handle modal delete button
    const modalDeleteBtn = document.querySelector('.modal-delete-btn');
    if (modalDeleteBtn) {
        modalDeleteBtn.addEventListener('click', function() {
            const imageId = this.dataset.id;
            const card = document.querySelector(`.result-card[data-id="${imageId}"]`);
            
            // Confirm deletion
            if (confirm('Are you sure you want to delete this image?')) {
                // Hide the modal
                const modal = document.getElementById('imageModal');
                const bsModal = bootstrap.Modal.getInstance(modal);
                bsModal.hide();
                
                // Add removing animation class
                card.classList.add('removing');
                
                // Send delete request
                fetch(`/api/delete_image/${imageId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    }
                    throw new Error('Network response was not ok');
                })
                .then(data => {
                    // Remove card after animation completes
                    setTimeout(() => {
                        card.remove();
                        
                        // Show success toast
                        const toastContainer = document.querySelector('.toast-container');
                        if (toastContainer) {
                            const toast = document.createElement('div');
                            toast.className = 'toast';
                            toast.setAttribute('role', 'alert');
                            toast.setAttribute('aria-live', 'assertive');
                            toast.setAttribute('aria-atomic', 'true');
                            toast.innerHTML = `
                                <div class="toast-header">
                                    <strong class="me-auto">Success</strong>
                                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                                </div>
                                <div class="toast-body">
                                    Image deleted successfully.
                                </div>
                            `;
                            toastContainer.appendChild(toast);
                            const bsToast = new bootstrap.Toast(toast);
                            bsToast.show();
                            
                            // Remove toast after it's hidden
                            toast.addEventListener('hidden.bs.toast', function() {
                                toast.remove();
                            });
                        }
                        
                        // Update counts
                        updateCounts();
                    }, 300);
                })
                .catch(error => {
                    console.error('Error:', error);
                    card.classList.remove('removing');
                    alert('Failed to delete image. Please try again.');
                });
            }
        });
    }
}

/**
 * Sets up filtering and sorting functionality
 */
function setupFilteringAndSorting() {
    // Get filter and sort elements
    const filterDropdown = document.getElementById('filterDropdown');
    const sortDropdown = document.getElementById('sortDropdown');
    
    if (!filterDropdown || !sortDropdown) return;
    
    // Get filter and sort items
    const filterItems = filterDropdown.querySelectorAll('.dropdown-item');
    const sortItems = sortDropdown.querySelectorAll('.dropdown-item');
    
    // Get filter info elements
    const filterInfoText = document.getElementById('filterInfoText');
    const clearFilterBtn = document.getElementById('clearFilterBtn');
    
    // Get all result cards
    const resultCards = document.querySelectorAll('.result-card');
    
    // Initialize from session storage if available
    let currentFilter = sessionStorage.getItem('currentFilter') || 'all';
    let currentSort = sessionStorage.getItem('currentSort') || 'filename-asc';
    
    // Apply initial filter and sort
    applyFilter(currentFilter);
    applySort(currentSort);
    
    // Update active classes
    updateActiveClasses();
    
    // Handle filter clicks
    filterItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get filter value
            const filter = this.dataset.filter;
            
            // Apply filter
            applyFilter(filter);
            
            // Save to session storage
            sessionStorage.setItem('currentFilter', filter);
            
            // Update active classes
            updateActiveClasses();
        });
    });
    
    // Handle sort clicks
    sortItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get sort value
            const sort = this.dataset.sort;
            
            // Apply sort
            applySort(sort);
            
            // Save to session storage
            sessionStorage.setItem('currentSort', sort);
            
            // Update active classes
            updateActiveClasses();
        });
    });
    
    // Handle clear filter button
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Reset to 'all' filter
            applyFilter('all');
            
            // Save to session storage
            sessionStorage.setItem('currentFilter', 'all');
            
            // Update active classes
            updateActiveClasses();
        });
    }
    
    /**
     * Applies the specified filter to the result cards
     */
    function applyFilter(filter) {
        // Update current filter
        currentFilter = filter;
        
        // Show/hide cards based on filter
        resultCards.forEach(card => {
            const detectionResult = card.dataset.result;
            
            if (filter === 'all') {
                card.classList.remove('hidden-item');
            } else if (filter === 'detected' && detectionResult === 'true') {
                card.classList.remove('hidden-item');
            } else if (filter === 'not-detected' && detectionResult === 'false') {
                card.classList.remove('hidden-item');
            } else if (filter === 'unknown' && detectionResult === 'null') {
                card.classList.remove('hidden-item');
            } else {
                card.classList.add('hidden-item');
            }
        });
        
        // Update filter info text
        if (filterInfoText) {
            const subject = document.querySelector('.result-card')?.dataset.subject || 'items';
            
            if (filter === 'all') {
                filterInfoText.innerHTML = 'Showing all images';
                clearFilterBtn.classList.add('d-none');
            } else if (filter === 'detected') {
                filterInfoText.innerHTML = `Showing only images with <strong>${subject} detected</strong>`;
                clearFilterBtn.classList.remove('d-none');
            } else if (filter === 'not-detected') {
                filterInfoText.innerHTML = `Showing only images with <strong>no ${subject} detected</strong>`;
                clearFilterBtn.classList.remove('d-none');
            } else if (filter === 'unknown') {
                filterInfoText.innerHTML = 'Showing only images with <strong>unknown detection status</strong>';
                clearFilterBtn.classList.remove('d-none');
            }
        }
    }
    
    /**
     * Applies the specified sort to the result cards
     */
    function applySort(sort) {
        // Update current sort
        currentSort = sort;
        
        // Get the container
        const container = document.querySelector('.row.results-container');
        
        // Get all cards as array for sorting
        const cards = Array.from(resultCards);
        
        // Sort cards
        cards.sort((a, b) => {
            if (sort === 'filename-asc') {
                return a.dataset.filename.localeCompare(b.dataset.filename);
            } else if (sort === 'filename-desc') {
                return b.dataset.filename.localeCompare(a.dataset.filename);
            } else if (sort === 'status-asc') {
                // Sort by status: false, null, true (No, Unknown, Yes)
                const statusA = a.dataset.result;
                const statusB = b.dataset.result;
                
                if (statusA === 'false' && statusB !== 'false') return -1;
                if (statusA === 'null' && statusB === 'true') return -1;
                if (statusA === 'null' && statusB === 'false') return 1;
                if (statusA === 'true') return 1;
                if (statusB === 'true') return -1;
                return 0;
            } else if (sort === 'status-desc') {
                // Sort by status: true, null, false (Yes, Unknown, No)
                const statusA = a.dataset.result;
                const statusB = b.dataset.result;
                
                if (statusA === 'true' && statusB !== 'true') return -1;
                if (statusA === 'null' && statusB === 'false') return -1;
                if (statusA === 'null' && statusB === 'true') return 1;
                if (statusA === 'false') return 1;
                if (statusB === 'false') return -1;
                return 0;
            }
            return 0;
        });
        
        // Reorder cards in the DOM
        cards.forEach(card => {
            container.appendChild(card.parentElement);
        });
    }
    
    /**
     * Updates the active classes on filter and sort items
     */
    function updateActiveClasses() {
        // Update filter active class
        filterItems.forEach(item => {
            if (item.dataset.filter === currentFilter) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        // Update sort active class
        sortItems.forEach(item => {
            if (item.dataset.sort === currentSort) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }
}

/**
 * Updates the counts in the summary section
 */
function updateCounts() {
    const totalElement = document.querySelector('.summary-value:nth-child(2)');
    const detectedElement = document.querySelector('.summary-value:nth-child(5)');
    const notDetectedElement = document.querySelector('.summary-value:nth-child(8)');
    const unknownElement = document.querySelector('.summary-value:nth-child(11)');
    
    if (totalElement) {
        const resultCards = document.querySelectorAll('.result-card');
        const total = resultCards.length;
        
        let detected = 0;
        let notDetected = 0;
        let unknown = 0;
        
        resultCards.forEach(card => {
            const detectionResult = card.dataset.result;
            
            if (detectionResult === 'true') {
                detected++;
            } else if (detectionResult === 'false') {
                notDetected++;
            } else {
                unknown++;
            }
        });
        
        totalElement.textContent = total;
        
        if (detectedElement) detectedElement.textContent = detected;
        if (notDetectedElement) notDetectedElement.textContent = notDetected;
        if (unknownElement) unknownElement.textContent = unknown;
    }
}
