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
    // Get all thumbnail images
    const thumbnails = document.querySelectorAll('.thumbnail');
    const imageModal = document.getElementById('imageModal');
    
    // Check if modal and thumbnails exist
    if (!imageModal || thumbnails.length === 0) {
        console.log('Image modal or thumbnails not found, skipping setup');
        return;
    }
    
    console.log(`Found ${thumbnails.length} thumbnails to setup for modal display`);
    
    // Create Bootstrap modal instance
    const modal = new bootstrap.Modal(imageModal);
    
    // Reference modal elements once
    const fullImage = document.getElementById('fullImage');
    const imageFilename = document.getElementById('imageFilename');
    const imageFlareStatus = document.getElementById('imageFlareStatus');
    const modalDeleteBtn = document.getElementById('modal-delete-btn');
    
    // Setup click handlers for all thumbnails
    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', function(e) {
            // Prevent default behavior and propagation
            e.preventDefault();
            e.stopPropagation();
            
            // Get data attributes
            const fullImageData = this.getAttribute('data-image');
            const filename = this.getAttribute('data-filename');
            const detectionStatus = this.getAttribute('data-detection-status');
            const index = this.getAttribute('data-index');
            const subject = document.getElementById('filterDropdown')?.getAttribute('data-subject') || 'Object';
            
            console.log(`Thumbnail clicked for ${filename}, status: ${detectionStatus}, index: ${index}`);
            
            // Set modal content
            if (fullImage) fullImage.src = fullImageData;
            if (imageFilename) imageFilename.textContent = filename;
            
            // Set status with appropriate styling
            if (imageFlareStatus) {
                let statusHtml = '';
                if (detectionStatus === 'true') {
                    statusHtml = `<span class="result-true"><i class="fas fa-check-circle"></i> ${subject} Detected: Yes</span>`;
                } else if (detectionStatus === 'false') {
                    statusHtml = `<span class="result-false"><i class="fas fa-times-circle"></i> ${subject} Detected: No</span>`;
                } else {
                    statusHtml = `<span class="result-unknown"><i class="fas fa-question-circle"></i> ${subject} Detected: Unknown</span>`;
                }
                imageFlareStatus.innerHTML = statusHtml;
            }
            
            // Set delete button data
            if (modalDeleteBtn) {
                modalDeleteBtn.setAttribute('data-index', index);
                modalDeleteBtn.setAttribute('data-filename', filename);
                
                // Add click event to the delete button
                modalDeleteBtn.onclick = function() {
                    const filenameToDelete = this.getAttribute('data-filename');
                    const indexToDelete = this.getAttribute('data-index');
                    
                    // Close the current modal
                    modal.hide();
                    
                    // Show confirmation modal
                    const deleteConfirmModal = document.getElementById('deleteConfirmModal');
                    if (deleteConfirmModal) {
                        const filenamePlaceholder = document.getElementById('filename-to-delete');
                        if (filenamePlaceholder) filenamePlaceholder.textContent = filenameToDelete;
                        
                        const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
                        if (confirmDeleteBtn) {
                            // Clear previous event listeners
                            const newBtn = confirmDeleteBtn.cloneNode(true);
                            confirmDeleteBtn.parentNode.replaceChild(newBtn, confirmDeleteBtn);
                            
                            // Add new event listener
                            newBtn.addEventListener('click', function() {
                                // Send delete request
                                fetch(`/api/delete_image/${indexToDelete}`, {
                                    method: 'DELETE'
                                })
                                .then(response => response.json())
                                .then(data => {
                                    if (data.success) {
                                        // Close the confirmation modal
                                        const bsConfirmModal = bootstrap.Modal.getInstance(deleteConfirmModal);
                                        bsConfirmModal.hide();
                                        
                                        // Remove the item from the page with animation
                                        const itemToRemove = document.querySelector(`.result-item[data-index="${indexToDelete}"]`);
                                        if (itemToRemove) {
                                            itemToRemove.classList.add('image-removed');
                                            setTimeout(() => {
                                                itemToRemove.remove();
                                                
                                                // Update counts if the function exists
                                                if (typeof updateCounts === 'function') {
                                                    updateCounts(data);
                                                }
                                                
                                                // Show toast notification
                                                showToast('Image deleted successfully');
                                            }, 500);
                                        }
                                    } else {
                                        alert('Error deleting image: ' + (data.error || 'Unknown error'));
                                    }
                                })
                                .catch(error => {
                                    console.error('Error:', error);
                                    alert('Failed to delete image. Please try again.');
                                });
                            });
                        }
                        
                        // Show the confirmation modal
                        const bsConfirmModal = new bootstrap.Modal(deleteConfirmModal);
                        bsConfirmModal.show();
                    }
                };
            }
            
            // Show the modal
            modal.show();
        });
    });
}

/**
 * Sets up filtering and sorting functionality
 */
function setupFilteringAndSorting() {
    console.log('Starting setupFilteringAndSorting');
    
    // Get filter and sort elements
    const filterDropdown = document.getElementById('filterDropdown');
    const sortDropdown = document.getElementById('sortDropdown');
    
    if (!filterDropdown || !sortDropdown) {
        console.error('Filter or sort dropdown not found in DOM');
        return;
    }
    
    console.log('Filter dropdown found:', filterDropdown.id);
    console.log('Sort dropdown found:', sortDropdown.id);
    
    // Get filter and sort items
    const filterItems = filterDropdown.querySelectorAll('.dropdown-item');
    const sortItems = sortDropdown.querySelectorAll('.dropdown-item');
    
    console.log('Filter items found:', filterItems.length);
    console.log('Sort items found:', sortItems.length);
    
    // Get filter info elements
    const filterInfoText = document.getElementById('filterInfo');
    
    // Get all result items
    const resultItems = document.querySelectorAll('.result-item');
    
    console.log('Result items found:', resultItems.length);
    
    // Debug: log data attributes of first few result items
    if (resultItems.length > 0) {
        console.log('Sample result item attributes:');
        for (let i = 0; i < Math.min(3, resultItems.length); i++) {
            const item = resultItems[i];
            console.log(`Item ${i}:`, {
                'data-detection-status': item.getAttribute('data-detection-status'),
                'data-filename': item.getAttribute('data-filename'),
                'data-subject': item.getAttribute('data-subject'),
                'classList': Array.from(item.classList)
            });
        }
    }
    
    // Initialize from session storage if available
    let currentFilter = sessionStorage.getItem('currentFilter') || 'all';
    let currentSort = sessionStorage.getItem('currentSort') || 'filename-asc';
    
    console.log('Initial filter from session storage:', currentFilter);
    console.log('Initial sort from session storage:', currentSort);
    
    // Clear any potentially bad stored values
    if (!['all', 'detected', 'not-detected', 'unknown'].includes(currentFilter)) {
        console.warn('Invalid filter value in session storage, resetting to "all"');
        currentFilter = 'all';
        sessionStorage.setItem('currentFilter', currentFilter);
    }
    
    // Apply initial filter and sort
    applyFilterAndSort();
    
    // Update active classes
    updateActiveClasses();
    
    // Handle filter clicks
    filterItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            console.log('Filter clicked:', this.dataset.filter);
            
            // Update active class
            filterItems.forEach(i => i.classList.remove('active-option'));
            this.classList.add('active-option');
            
            // Update current filter
            currentFilter = this.dataset.filter;
            
            // Apply filter and sort
            applyFilterAndSort();
            
            // Save to session storage
            sessionStorage.setItem('currentFilter', currentFilter);
        });
    });
    
    // Handle sort clicks
    sortItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            console.log('Sort clicked:', this.dataset.sort);
            
            // Update active class
            sortItems.forEach(i => i.classList.remove('active-option'));
            this.classList.add('active-option');
            
            // Update current sort
            currentSort = this.dataset.sort;
            
            // Apply filter and sort
            applyFilterAndSort();
            
            // Save to session storage
            sessionStorage.setItem('currentSort', currentSort);
        });
    });
    
    /**
     * Applies both filtering and sorting based on current selections
     */
    function applyFilterAndSort() {
        console.log('Applying filter:', currentFilter, 'and sort:', currentSort);
        
        // Get the current subject from data attribute
        let subject = getSubjectFromDom();
        console.log('Current subject:', subject);
        
        // First, filter the items
        let visibleCount = 0;
        let hiddenCount = 0;
        
        resultItems.forEach(item => {
            const detectionStatus = item.getAttribute('data-detection-status');
            const itemSubject = item.getAttribute('data-subject') || subject;
            const filename = item.getAttribute('data-filename');
            
            console.log(`Filtering item: ${filename}, subject: ${itemSubject}, status: ${detectionStatus}`);
            
            let visible = false;
            
            if (currentFilter === 'all') {
                visible = true;
            } else if (currentFilter === 'detected' && detectionStatus === 'true') {
                visible = true;
            } else if (currentFilter === 'not-detected' && detectionStatus === 'false') {
                visible = true;
            } else if (currentFilter === 'unknown' && detectionStatus === 'unknown') {
                visible = true;
            }
            
            if (visible) {
                console.log(`  - Showing item: ${filename} (matches filter: ${currentFilter})`);
                item.classList.remove('hidden-item');
                visibleCount++;
            } else {
                console.log(`  - Hiding item: ${filename} (doesn't match filter: ${currentFilter})`);
                item.classList.add('hidden-item');
                hiddenCount++;
            }
        });
        
        console.log(`Filtering complete: ${visibleCount} visible items, ${hiddenCount} hidden items`);
        
        // Count visible items after filtering
        const visibleItems = Array.from(resultItems).filter(item => !item.classList.contains('hidden-item'));
        console.log(`Filtered to ${visibleItems.length} visible items out of ${resultItems.length} total`);
        
        // Then, sort the visible items
        const resultsContainer = document.getElementById('results-container');
        
        if (!resultsContainer) {
            console.error('Results container not found');
            return;
        }
        
        console.log('Sorting visible items');
        visibleItems.sort((a, b) => {
            if (currentSort === 'filename-asc') {
                return a.getAttribute('data-filename').localeCompare(b.getAttribute('data-filename'));
            } else if (currentSort === 'filename-desc') {
                return b.getAttribute('data-filename').localeCompare(a.getAttribute('data-filename'));
            } else if (currentSort === 'status-asc') {
                // Sort order: false, unknown, true
                const aStatus = a.getAttribute('data-detection-status');
                const bStatus = b.getAttribute('data-detection-status');
                
                console.log(`Comparing for sort: ${a.getAttribute('data-filename')} (${aStatus}) vs ${b.getAttribute('data-filename')} (${bStatus})`);
                
                if (aStatus === bStatus) return 0;
                if (aStatus === 'false') return -1;
                if (bStatus === 'false') return 1;
                if (aStatus === 'unknown') return -1;
                if (bStatus === 'unknown') return 1;
                return 0;
            } else if (currentSort === 'status-desc') {
                // Sort order: true, unknown, false
                const aStatus = a.getAttribute('data-detection-status');
                const bStatus = b.getAttribute('data-detection-status');
                
                if (aStatus === bStatus) return 0;
                if (aStatus === 'true') return -1;
                if (bStatus === 'true') return 1;
                if (aStatus === 'unknown') return -1;
                if (bStatus === 'unknown') return 1;
                return 0;
            }
            return 0;
        });
        
        // Reorder the DOM elements
        console.log('Reordering DOM elements');
        visibleItems.forEach(item => {
            resultsContainer.appendChild(item);
        });
        
        // Update filter info text
        updateFilterInfoText();
    }
    
    /**
     * Gets the current subject from the DOM in a reliable way
     */
    function getSubjectFromDom() {
        // Try multiple sources to get the subject reliably
        
        // First try: get from dropdown button with data-subject
        const fromDropdown = filterDropdown.getAttribute('data-subject');
        if (fromDropdown) {
            console.log('Got subject from dropdown:', fromDropdown);
            return fromDropdown;
        }
        
        // Second try: get from result items if available
        if (resultItems.length > 0) {
            const fromItem = resultItems[0].getAttribute('data-subject');
            if (fromItem) {
                console.log('Got subject from first result item:', fromItem);
                return fromItem;
            }
        }
        
        // Fallback
        console.log('Using fallback subject: "item"');
        return 'item';
    }
    
    /**
     * Updates the filter info text based on current selections
     */
    function updateFilterInfoText() {
        if (!filterInfoText) {
            console.warn('Filter info text element not found');
            return;
        }
        
        let filterText = '';
        let sortText = '';
        
        // Get subject from the DOM
        const subject = getSubjectFromDom();
        console.log('Using subject for filter text:', subject);
        
        // Handle pluralization
        const pluralSuffix = subject.endsWith('s') ? '' : 's';
        
        // Get filter text
        if (currentFilter === 'all') {
            filterText = 'all images';
        } else if (currentFilter === 'detected') {
            filterText = `images with ${subject}${pluralSuffix} detected`;
        } else if (currentFilter === 'not-detected') {
            filterText = `images with no ${subject}${pluralSuffix}`;
        } else if (currentFilter === 'unknown') {
            filterText = 'images with unknown status';
        }
        
        // Get sort text
        if (currentSort === 'filename-asc') {
            sortText = 'filename (A-Z)';
        } else if (currentSort === 'filename-desc') {
            sortText = 'filename (Z-A)';
        } else if (currentSort === 'status-asc') {
            sortText = `${subject} status (No → Yes)`;
        } else if (currentSort === 'status-desc') {
            sortText = `${subject} status (Yes → No)`;
        }
        
        // Update the info text
        const newText = `Showing ${filterText}, sorted by ${sortText}`;
        console.log('Updating filter info text:', newText);
        filterInfoText.textContent = newText;
    }
    
    /**
     * Updates the active classes on filter and sort items
     */
    function updateActiveClasses() {
        // Update filter active class
        filterItems.forEach(item => {
            if (item.dataset.filter === currentFilter) {
                item.classList.add('active-option');
                console.log(`Set active filter option: ${item.dataset.filter}`);
            } else {
                item.classList.remove('active-option');
            }
        });
        
        // Update sort active class
        sortItems.forEach(item => {
            if (item.dataset.sort === currentSort) {
                item.classList.add('active-option');
                console.log(`Set active sort option: ${item.dataset.sort}`);
            } else {
                item.classList.remove('active-option');
            }
        });
    }
    
    console.log('setupFilteringAndSorting completed');
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
