/**
 * Accounts module for handling user management
 */

// Document ready handler
document.addEventListener('DOMContentLoaded', function() {
    // Initialize user list functionality if on that page
    if (document.getElementById('users-table-body')) {
        initUserList();
    }
});

/**
 * Initialize user list page functionality
 */
function initUserList() {
    // Attach event handlers
    attachEventHandlers();
}

/**
 * Load users with AJAX
 */
function loadUsers() {
    ajax.get("/accounts/admin/users/", function(err, data) {
        if (err) {
            showAlert('danger', 'Kullanıcılar yüklenirken hata oluştu: ' + err);
            return;
        }
        
        var tbody = document.getElementById('users-table-body');
        tbody.innerHTML = '';
        
        if (data.users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">Hiç kullanıcı yok.</td></tr>';
            return;
        }
        
        data.users.forEach(function(user) {
            var row = document.createElement('tr');
            row.setAttribute('data-user-id', user.id);
            
            var usernameCell = document.createElement('td');
            usernameCell.textContent = user.username;
            
            var nameCell = document.createElement('td');
            nameCell.textContent = user.full_name;
            
            var emailCell = document.createElement('td');
            emailCell.textContent = user.email;
            
            var teamCell = document.createElement('td');
            teamCell.textContent = user.team;
            
            var actionsCell = document.createElement('td');
            
            var editBtn = document.createElement('button');
            editBtn.className = 'btn btn-warning btn-sm edit-user-btn';
            editBtn.setAttribute('data-user-id', user.id);
            editBtn.textContent = '✏️';
            
            var deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-danger btn-sm delete-user-btn';
            deleteBtn.setAttribute('data-user-id', user.id);
            deleteBtn.textContent = '🗑️';
            
            actionsCell.appendChild(editBtn);
            actionsCell.appendChild(document.createTextNode(' '));
            actionsCell.appendChild(deleteBtn);
            
            row.appendChild(usernameCell);
            row.appendChild(nameCell);
            row.appendChild(emailCell);
            row.appendChild(teamCell);
            row.appendChild(actionsCell);
            
            tbody.appendChild(row);
        });
        
        // Reattach event handlers
        attachEventHandlers();
    });
}

/**
 * Show form in modal
 */
function showFormInModal(url, title) {
    ajax.get(url, function(err, data) {
        if (err) {
            showAlert('danger', 'Form yüklenirken hata oluştu: ' + err);
            return;
        }
        
        var modalLabel = document.getElementById('userModalLabel');
        var modalBody = document.getElementById('userModalBody');
        
        modalLabel.textContent = title;
        modalBody.innerHTML = data.html;
        
        // Setup form submission
        var form = modalBody.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Create a proper object for the form data
                var formData = {};
                var formElements = form.querySelectorAll('input, select, textarea');
                
                formElements.forEach(function(element) {
                    if (element.name && element.name !== 'csrfmiddlewaretoken') {
                        formData[element.name] = element.value;
                    }
                });
                
                // Get the CSRF token
                var csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]').value;
                
                // Make a direct AJAX request with proper headers
                var xhr = new XMLHttpRequest();
                xhr.open('POST', form.getAttribute('action'), true);
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                xhr.setRequestHeader('X-CSRFToken', csrfToken);
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            try {
                                var data = JSON.parse(xhr.responseText);
                                if (data.success) {
                                    var userModal = bootstrap.Modal.getInstance(document.getElementById('userModal'));
                                    userModal.hide();
                                    showAlert('success', data.message);
                                    loadUsers();
                                }
                            } catch (e) {
                                showAlert('danger', 'Server response was not valid JSON');
                            }
                        } else {
                            showAlert('danger', 'İşlem sırasında hata oluştu: ' + xhr.statusText);
                        }
                    }
                };
                
                // Serialize the form data
                var formDataString = Object.keys(formData).map(function(key) {
                    return encodeURIComponent(key) + '=' + encodeURIComponent(formData[key]);
                }).join('&');
                
                // Add CSRF token
                formDataString += '&csrfmiddlewaretoken=' + encodeURIComponent(csrfToken);
                
                xhr.send(formDataString);
            });
        }
        
        var userModal = new bootstrap.Modal(document.getElementById('userModal'));
        userModal.show();
    });
}

/**
 * Delete user with confirmation modal
 */
function deleteUser(userId) {
    // Find the username for better UX
    var userRow = document.querySelector('tr[data-user-id="' + userId + '"]');
    var username = userRow ? userRow.querySelector('td:first-child').textContent : '';
    
    // Set the username in the modal
    document.getElementById('deleteUserName').textContent = username;
    
    // Set up the confirm delete button
    var confirmBtn = document.getElementById('confirmDeleteBtn');
    
    // Remove previous event listeners
    var newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    // Add the new event listener
    newConfirmBtn.addEventListener('click', function() {
        var url = '/accounts/admin/users/' + userId + '/delete/';
        
        ajax.delete(url, function(err, data) {
            if (err) {
                showAlert('danger', 'Kullanıcı silinirken hata oluştu: ' + err);
                return;
            }
            
            // Hide the modal
            var deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
            deleteModal.hide();
            
            showAlert('success', 'Kullanıcı başarıyla silindi.');
            loadUsers();
        });
    });
    
    // Show the modal
    var deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    deleteModal.show();
}

/**
 * Show alert
 */
function showAlert(type, message) {
    var alertContainer = document.getElementById('alert-container');
    
    var alert = document.createElement('div');
    alert.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alert.setAttribute('role', 'alert');
    
    alert.innerHTML = message + 
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
    
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 3 seconds
    setTimeout(function() {
        var bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    }, 3000);
}

/**
 * Attach event handlers
 */
function attachEventHandlers() {
    // Add user button
    var addUserBtn = document.getElementById('add-user-btn');
    if (addUserBtn) {
        addUserBtn.removeEventListener('click', addUserHandler);
        addUserBtn.addEventListener('click', addUserHandler);
    }
    
    // Edit user buttons
    var editBtns = document.querySelectorAll('.edit-user-btn');
    editBtns.forEach(function(btn) {
        btn.removeEventListener('click', editUserHandler);
        btn.addEventListener('click', editUserHandler);
    });
    
    // Delete user buttons
    var deleteBtns = document.querySelectorAll('.delete-user-btn');
    deleteBtns.forEach(function(btn) {
        btn.removeEventListener('click', deleteUserHandler);
        btn.addEventListener('click', deleteUserHandler);
    });
}

/**
 * Event handlers
 */
function addUserHandler(e) {
    e.preventDefault();
    showFormInModal("/accounts/admin/users/create/", 'Yeni Kullanıcı Ekle');
}

function editUserHandler() {
    var userId = this.getAttribute('data-user-id');
    showFormInModal("/accounts/admin/users/" + userId + "/edit/", 'Kullanıcıyı Güncelle');
}

function deleteUserHandler() {
    var userId = this.getAttribute('data-user-id');
    deleteUser(userId);
} 