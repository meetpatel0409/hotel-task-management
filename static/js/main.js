function init() {
    console.log("HotelTask main.js: Initializing scripts...");
    
    // Set min attribute and initialize Flatpickr for datetime inputs to prevent past selections and show custom calendar
    function setMinDateTime() {
        if (typeof flatpickr !== 'undefined') {
            flatpickr('input[type="datetime-local"]', {
                enableTime: true,
                dateFormat: "Y-m-d\\TH:i", // matches HTML5 datetime-local format!
                altInput: true,
                altFormat: "F j, Y - h:i K", // User friendly format: e.g. June 15, 2026 - 06:19 PM
                minDate: new Date(),
                theme: "dark",
                time_24hr: false
            });
        } else {
            // Fallback to native datetime-local behavior if Flatpickr CDN fails to load
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const minDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
            
            const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
            datetimeInputs.forEach(input => {
                input.min = minDateTime;
                
                const triggerPicker = function() {
                    try {
                        input.showPicker();
                    } catch (e) {
                        console.log("input.showPicker() not supported or blocked: ", e);
                    }
                };
                input.addEventListener('click', triggerPicker);
                input.addEventListener('focus', triggerPicker);
            });
        }
    }
    setMinDateTime();
    // 1. Alert Auto-dismiss after 4 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 4000);
        
        // Manual dismiss
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                alert.remove();
            });
        }
    });

    // 2. Mobile Navigation Toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function () {
            sidebar.classList.toggle('active');
        });
        
        // Close sidebar if clicking outside on mobile
        document.addEventListener('click', function (event) {
            if (!sidebar.contains(event.target) && !menuToggle.contains(event.target) && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
            }
        });
    }

    // 3. Login Role Chip Toggles (Removed - system auto-routes based on email registry)

    // 4. Modal Interactions
    const modalTriggers = document.querySelectorAll('[data-open-modal]');
    const modalCloses = document.querySelectorAll('[data-close-modal]');
    
    modalTriggers.forEach(function (trigger) {
        trigger.addEventListener('click', function () {
            setMinDateTime();
            const modalId = trigger.getAttribute('data-open-modal');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('active');
                
                // If there's a task ID passed as an attribute, inject it
                const taskId = trigger.getAttribute('data-task-id');
                const taskTitle = trigger.getAttribute('data-task-title');
                const taskCategory = trigger.getAttribute('data-task-category');
                
                if (taskId) {
                    const idInput = modal.querySelector('.modal-task-id-input');
                    if (idInput) idInput.value = taskId;
                    
                    const titlePlaceholder = modal.querySelector('.modal-task-title-placeholder');
                    if (titlePlaceholder && taskTitle) titlePlaceholder.textContent = taskTitle;
                    
                    // If modal has a dynamic action form
                    const actionForm = modal.querySelector('.modal-action-form');
                    if (actionForm) {
                        const originalAction = actionForm.getAttribute('data-original-action');
                        if (originalAction) {
                            actionForm.action = originalAction.replace('0', taskId);
                        }
                    }
                    
                    // Auto-select department in the modal's department dropdown based on task category
                    const modalDeptSelect = modal.querySelector('#modal-reassign-dept');
                    if (modalDeptSelect && taskCategory) {
                        const categoryToDeptMap = {
                            'Room Cleaning': 'Housekeeping',
                            'Maintenance': 'Maintenance',
                            'Restaurant Prep': 'Kitchen',
                            'Laundry': 'Laundry',
                            'Guest Service': 'Front Office',
                            'Inventory Check': ''
                        };
                        const targetDept = categoryToDeptMap[taskCategory] || '';
                        modalDeptSelect.value = targetDept;
                        
                        // Trigger change event to update employee select options
                        const event = new Event('change');
                        modalDeptSelect.dispatchEvent(event);
                    }
                }
            }
        });
    });

    modalCloses.forEach(function (close) {
        close.addEventListener('click', function () {
            const modal = close.closest('.modal');
            if (modal) {
                modal.classList.remove('active');
            }
        });
    });

    // Close modal if clicking overlay background
    const modals = document.querySelectorAll('.modal');
    modals.forEach(function (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });

    // 5. Image File Upload Previewing
    const previewContainers = document.querySelectorAll('.image-preview-container');
    previewContainers.forEach(function (container) {
        const fileInput = container.querySelector('input[type="file"]');
        const previewImg = container.querySelector('.image-preview-img');
        const previewIcon = container.querySelector('.image-preview-icon');
        const previewText = container.querySelector('.image-preview-text');
        
        container.addEventListener('click', function () {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.addEventListener('load', function () {
                    previewImg.src = reader.result;
                    previewImg.style.display = 'inline-block';
                    if (previewIcon) previewIcon.style.display = 'none';
                    if (previewText) previewText.textContent = file.name;
                });
                reader.readAsDataURL(file);
            }
        });
    });

    // 6. Chart rendering for admin and manager dashboards (using Chart.js from CDN)
    const statsChartElement = document.getElementById('statusOverviewChart');
    const deptChartElement = document.getElementById('deptPerformanceChart');
    const slaChartElement = document.getElementById('slaOverviewChart');
    const avgResChartElement = document.getElementById('avgResolutionChart');
    
    if (statsChartElement || deptChartElement || slaChartElement || avgResChartElement) {
        // Fetch chart statistics from our JSON endpoint
        fetch('/api/reports-data')
            .then(response => response.json())
            .then(data => {
                // Render Status Chart
                if (statsChartElement && typeof Chart !== 'undefined') {
                    const ctx = statsChartElement.getContext('2d');
                    new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: ['Pending', 'In Progress', 'Completed (Awaiting Review)', 'Approved', 'Rejected'],
                            datasets: [{
                                data: [
                                    data.status_overview.Pending,
                                    data.status_overview.InProgress,
                                    data.status_overview.Completed,
                                    data.status_overview.Approved,
                                    data.status_overview.Rejected
                                ],
                                backgroundColor: [
                                    '#f59e0b', // Pending (Amber)
                                    '#3b82f6', // In Progress (Blue)
                                    '#8b5cf6', // Completed (Purple)
                                    '#10b981', // Approved (Green)
                                    '#ef4444'  // Rejected (Red)
                                ],
                                borderWidth: 1,
                                borderColor: 'rgba(255, 255, 255, 0.08)'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'bottom',
                                    labels: {
                                        color: '#9ca3af',
                                        font: { family: 'Inter', size: 11 }
                                    }
                                }
                            }
                        }
                    });
                }

                // Render Department Performance Bar Chart
                if (deptChartElement && typeof Chart !== 'undefined') {
                    const ctx = deptChartElement.getContext('2d');
                    const depts = Object.keys(data.department_performance);
                    const completedData = depts.map(d => data.department_performance[d].completed);
                    const pendingData = depts.map(d => data.department_performance[d].pending);
                    
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: depts,
                            datasets: [
                                {
                                    label: 'Completed Tasks',
                                    data: completedData,
                                    backgroundColor: '#10b981',
                                    borderRadius: 4
                                },
                                {
                                    label: 'Pending Tasks',
                                    data: pendingData,
                                    backgroundColor: '#f59e0b',
                                    borderRadius: 4
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                x: {
                                    grid: { display: false },
                                    ticks: { color: '#9ca3af', font: { family: 'Inter' } }
                                },
                                y: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: '#9ca3af', font: { family: 'Inter' } }
                                }
                            },
                            plugins: {
                                legend: {
                                    position: 'bottom',
                                    labels: {
                                        color: '#9ca3af',
                                        font: { family: 'Inter', size: 11 }
                                    }
                                }
                            }
                        }
                    });
                }

                // Render SLA Compliance Doughnut Chart
                if (slaChartElement && typeof Chart !== 'undefined') {
                    const ctx = slaChartElement.getContext('2d');
                    new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: ['Met', 'Breached'],
                            datasets: [{
                                data: [
                                    data.sla_overview.Met,
                                    data.sla_overview.Breached
                                ],
                                backgroundColor: [
                                    '#10b981', // Met (Green)
                                    '#ef4444'  // Breached (Red)
                                ],
                                borderWidth: 1,
                                borderColor: 'rgba(255, 255, 255, 0.08)'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'bottom',
                                    labels: {
                                        color: '#9ca3af',
                                        font: { family: 'Inter', size: 11 }
                                    }
                                }
                            }
                        }
                    });
                }

                // Render Average Resolution Time Bar Chart
                if (avgResChartElement && typeof Chart !== 'undefined') {
                    const ctx = avgResChartElement.getContext('2d');
                    const depts = Object.keys(data.dept_avg_resolution);
                    const avgHours = Object.values(data.dept_avg_resolution);
                    
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: depts,
                            datasets: [
                                {
                                    label: 'Average Hours to Resolve',
                                    data: avgHours,
                                    backgroundColor: '#d97706',
                                    borderRadius: 4
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                x: {
                                    grid: { display: false },
                                    ticks: { color: '#9ca3af', font: { family: 'Inter' } }
                                },
                                y: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: '#9ca3af', font: { family: 'Inter' } }
                                }
                            },
                            plugins: {
                                legend: {
                                    position: 'bottom',
                                    labels: {
                                        color: '#9ca3af',
                                        font: { family: 'Inter', size: 11 }
                                    }
                                }
                            }
                        }
                    });
                }
            })
            .catch(err => console.error('Error fetching reports metrics:', err));
    }

    // 7. Dependent Department & Employee Selection Filtering
    const schedulerDeptSelect = document.getElementById('task-department');
    const schedulerAssigneeSelect = document.getElementById('assignee');
    
    function filterEmployees(deptSelect, assigneeSelect) {
        if (!deptSelect || !assigneeSelect) return;
        
        const selectedDept = deptSelect.value;
        const optgroups = assigneeSelect.querySelectorAll('optgroup');
        const defaultOption = assigneeSelect.querySelector('option[value=""]');
        
        if (!selectedDept) {
            assigneeSelect.disabled = true;
            if (defaultOption) defaultOption.textContent = '-- Choose Department First --';
            assigneeSelect.value = '';
            optgroups.forEach(group => group.style.display = 'none');
        } else {
            assigneeSelect.disabled = false;
            if (defaultOption) defaultOption.textContent = '-- Choose Staff --';
            assigneeSelect.value = '';
            
            optgroups.forEach(group => {
                if (group.label === selectedDept) {
                    group.style.display = '';
                } else {
                    group.style.display = 'none';
                }
            });
        }
    }
    
    if (schedulerDeptSelect && schedulerAssigneeSelect) {
        schedulerDeptSelect.addEventListener('change', function() {
            filterEmployees(schedulerDeptSelect, schedulerAssigneeSelect);
        });
        // Run once on load
        filterEmployees(schedulerDeptSelect, schedulerAssigneeSelect);
    }
    
    // Modal-based reassign department dependent dropdown
    const modalDeptSelect = document.getElementById('modal-reassign-dept');
    const modalAssigneeSelect = document.getElementById('reassign-employee');
    
    if (modalDeptSelect && modalAssigneeSelect) {
        modalDeptSelect.addEventListener('change', function() {
            filterEmployees(modalDeptSelect, modalAssigneeSelect);
        });
    }

    // 8. Interactive Stats Cards & Department Checklist Filtering
    const interactiveCards = document.querySelectorAll('.interactive-card');
    const checklistTbody = document.getElementById('checklist-tbody');
    const noTasksRow = document.getElementById('no-tasks-row');
    const tableDeptFilter = document.getElementById('table-dept-filter');
    
    console.log("HotelTask main.js: interactiveCards found:", interactiveCards.length);
    console.log("HotelTask main.js: checklistTbody found:", !!checklistTbody);
    
    if (interactiveCards.length > 0 && checklistTbody) {
        function applyChecklistFilters() {
            const activeCard = document.querySelector('.interactive-card.active-filter');
            const filter = activeCard ? activeCard.getAttribute('data-filter') : 'all';
            const deptFilter = tableDeptFilter ? tableDeptFilter.value : 'all';
            
            console.log("HotelTask main.js: Applying filters -> status filter:", filter, "| department filter:", deptFilter);
            
            const rows = checklistTbody.querySelectorAll('.task-row');
            let visibleCount = 0;
            
            rows.forEach((row, index) => {
                const status = row.getAttribute('data-status');
                const rowDept = row.getAttribute('data-department') || 'General';
                
                // 1. Status Filter
                let matchesStatus = false;
                if (filter === 'all') {
                    matchesStatus = true;
                } else if (filter === 'active') {
                    // Manager: Pending, In Progress, Rejected, Awaiting Handover
                    matchesStatus = (status === 'Pending' || status === 'In Progress' || status === 'Rejected' || status === 'Awaiting Handover');
                } else if (filter === 'awaiting') {
                    // Manager: Completed (awaiting verification)
                    matchesStatus = (status === 'Completed');
                } else if (filter === 'verified') {
                    // Manager: Approved
                    matchesStatus = (status === 'Approved');
                } else if (filter === 'completed') {
                    // HOD: Completed or Approved
                    matchesStatus = (status === 'Completed' || status === 'Approved');
                } else {
                    // Exact match (e.g. HOD stats: Pending, In Progress)
                    matchesStatus = (status === filter);
                }
                
                // 2. Department Filter
                let matchesDept = (deptFilter === 'all' || rowDept === deptFilter);
                
                if (matchesStatus && matchesDept) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            console.log("HotelTask main.js: Filtering complete. Visible rows count:", visibleCount);
            
            if (noTasksRow) {
                if (visibleCount === 0) {
                    noTasksRow.style.display = '';
                } else {
                    noTasksRow.style.display = 'none';
                }
            }
        }
        
        interactiveCards.forEach(card => {
            card.addEventListener('click', function() {
                console.log("HotelTask main.js: Stat card clicked ->", card.getAttribute('data-filter'));
                interactiveCards.forEach(c => c.classList.remove('active-filter'));
                card.classList.add('active-filter');
                applyChecklistFilters();
                
                // Auto-scroll to correct section on mobile/tablet viewports
                if (window.innerWidth <= 768) {
                    const filter = card.getAttribute('data-filter');
                    let targetId = 'checklist-section';
                    if (filter === 'awaiting') {
                        const verificationFeed = document.getElementById('verification-feed-section');
                        if (verificationFeed) {
                            targetId = 'verification-feed-section';
                        }
                    }
                    const targetSection = document.getElementById(targetId);
                    if (targetSection) {
                        targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }
            });
        });
        
        if (tableDeptFilter) {
            tableDeptFilter.addEventListener('change', function() {
                console.log("HotelTask main.js: Department dropdown changed ->", tableDeptFilter.value);
                applyChecklistFilters();
            });
        }
        
        // Auto-select "Global Actions / Total Assigned" filter card on page load
        const allFilterCard = Array.from(interactiveCards).find(c => c.getAttribute('data-filter') === 'all');
        if (allFilterCard) {
            allFilterCard.classList.add('active-filter');
            applyChecklistFilters(); // Trigger filter application on page load
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
