// AJAX utility functions
const ajax = {
    // GET request
    get: function(url, callback) {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    callback(null, JSON.parse(xhr.responseText));
                } else {
                    callback(xhr.statusText);
                }
            }
        };
        xhr.send();
    },

    // POST request
    post: function(url, data, callback) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-CSRFTOKEN', getCookie('csrftoken'));
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200 || xhr.status === 201) {
                    callback(null, JSON.parse(xhr.responseText));
                } else {
                    callback(xhr.statusText);
                }
            }
        };
        xhr.send(JSON.stringify(data));
    },

    // PUT request
    put: function(url, data, callback) {
        const xhr = new XMLHttpRequest();
        xhr.open('PUT', url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-CSRFTOKEN', getCookie('csrftoken'));
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    callback(null, JSON.parse(xhr.responseText));
                } else {
                    callback(xhr.statusText);
                }
            }
        };
        xhr.send(JSON.stringify(data));
    },

    // DELETE request
    delete: function(url, callback) {
        const xhr = new XMLHttpRequest();
        xhr.open('DELETE', url, true);
        xhr.setRequestHeader('X-CSRFTOKEN', getCookie('csrftoken'));
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 204 || xhr.status === 200) {
                    callback(null);
                } else {
                    callback(xhr.statusText);
                }
            }
        };
        xhr.send();
    }
};

/**
 * Improved utility function to get CSRF token from cookies
 * Required for AJAX POST, PUT, DELETE requests
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Format date and time
 * @param {string} dateString - ISO date string
 * @param {string} locale - Locale for formatting (default: 'tr-TR')
 * @returns {string} Formatted date and time
 */
function formatDateTime(dateString, locale = 'tr-TR') {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString(locale);
}

/**
 * Handle AJAX errors and display appropriate messages
 * @param {object} xhr - XMLHttpRequest object
 */
function handleAjaxError(xhr) {
    console.error('AJAX Error:', xhr);
    
    // Get error message
    let errorMsg = 'Bir hata oluştu!';
    
    if (xhr.responseJSON) {
        if (xhr.responseJSON.detail) {
            errorMsg = xhr.responseJSON.detail;
        } else if (xhr.responseJSON.non_field_errors) {
            errorMsg = xhr.responseJSON.non_field_errors.join(', ');
        } else {
            // Try to get first error message
            const firstErrorKey = Object.keys(xhr.responseJSON)[0];
            if (firstErrorKey && xhr.responseJSON[firstErrorKey]) {
                errorMsg = `${firstErrorKey}: ${xhr.responseJSON[firstErrorKey]}`;
            }
        }
    }
    
    // Display error message
    if (typeof toastr !== 'undefined') {
        toastr.error(errorMsg);
    } else {
        alert(`Hata: ${errorMsg}`);
    }
}

/**
 * Check if a user has a team and required permissions
 * @param {string} teamType - Required team type (optional)
 * @returns {boolean} Whether user has required permissions
 */
function hasTeamPermission(teamType = null) {
    // This assumes team type is set in a global variable or data attribute
    const userTeamType = document.querySelector('body').dataset.teamType || '';
    
    if (!userTeamType) {
        return false;
    }
    
    if (teamType && userTeamType !== teamType) {
        return false;
    }
    
    return true;
} 