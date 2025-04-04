/**
 * Aircraft Assembly Interface
 * Handles interactive assembly of aircraft parts
 */

$(document).ready(function() {
    // Initialize
    const assemblyId = $('#assembly-container').data('assembly-id');
    const aircraftType = $('#assembly-container').data('aircraft-type');
    
    // Update the skeleton when the page loads
    updateSkeletonDisplay();
    
    // Get available parts for this aircraft type
    loadAvailableParts();
    
    /**
     * Load available parts from the API
     */
    function loadAvailableParts() {
        $.ajax({
            url: `/assembly/api/available-parts/${aircraftType}/`,
            type: 'GET',
            success: function(response) {
                displayAvailableParts(response.parts);
                checkMissingParts(response.available_parts);
            },
            error: function(error) {
                toastr.error('Parçalar yüklenirken hata oluştu.');
                console.error('Error loading parts:', error);
            }
        });
    }
    
    /**
     * Display available parts in the parts panel
     */
    function displayAvailableParts(parts) {
        const partsPanel = $('#parts-panel');
        partsPanel.empty();
        
        if (parts.length === 0) {
            partsPanel.append('<div class="alert alert-warning">Bu uçak için kullanılabilir parça bulunamadı.</div>');
            return;
        }
        
        // Group parts by type
        const partsByType = {};
        parts.forEach(part => {
            if (!partsByType[part.part_type]) {
                partsByType[part.part_type] = [];
            }
            partsByType[part.part_type].push(part);
        });
        
        // Define part type display order
        const partTypeOrder = ['body', 'wing', 'tail', 'avionics'];
        
        // Create section for each part type in the specified order
        partTypeOrder.forEach(partType => {
            if (!partsByType[partType] || partsByType[partType].length === 0) {
                return; // Skip if no parts of this type
            }
            
            const partTypeDisplay = partsByType[partType][0].part_type_display;
            
            const typeSection = $(`
                <div class="mb-4 part-type-section" id="part-section-${partType}">
                    <h5 class="border-bottom pb-2">${partTypeDisplay} Parçaları</h5>
                    <div class="part-type-container" id="part-type-${partType}"></div>
                </div>
            `);
            
            const container = typeSection.find(`#part-type-${partType}`);
            
            // Add each part to its section
            partsByType[partType].forEach(part => {
                const partCard = $(`
                    <div class="part-card" data-part-id="${part.id}" data-part-type="${part.part_type}">
                        <div class="d-flex justify-content-between align-items-center">
                            <span>
                                <span class="badge bg-secondary">#${part.id}</span>
                                ${part.part_type_display}
                            </span>
                            <span class="aircraft-type-badge aircraft-type-${part.aircraft_type}">
                                ${part.aircraft_type_display}
                            </span>
                        </div>
                        <small class="text-muted d-block mt-1">Üretim: ${new Date(part.created_at).toLocaleString()}</small>
                    </div>
                `);
                
                partCard.on('click', function() {
                    selectPart($(this));
                });
                
                container.append(partCard);
            });
            
            partsPanel.append(typeSection);
        });
    }
    
    /**
     * Handle part selection
     */
    function selectPart(partCard) {
        const partType = partCard.data('part-type');
    
        if (partCard.hasClass('selected')) {
            // If already selected, deselect it
            partCard.removeClass('selected');
        } else {
            // Only allow one part of each type to be selected
            // First deselect any other parts of the same type
            $(`.part-card[data-part-type="${partType}"]`).removeClass('selected');
            // Then select this part
            partCard.addClass('selected');
        }
        
        // Update button text based on selection count
        updateAddButtonText();
    }
    
    /**
     * Update the "Add Part" button text based on selection count
     */
    function updateAddButtonText() {
        const selectedCount = $('.part-card.selected').length;
        if (selectedCount > 1) {
            $('#add-part-btn').text('Seçili Parçaları Ekle');
        } else {
            $('#add-part-btn').text('Seçili Parçayı Ekle');
        }
    }
    
    /**
     * Add selected parts to assembly
     */
    $('#add-part-btn').on('click', function() {
        const selectedParts = $('.part-card.selected');
        
        if (selectedParts.length === 0) {
            toastr.warning('Lütfen eklemek için bir parça seçin.');
            return;
        }
        
        // Collect all selected part IDs and validate
        const partIds = [];
        const selectedPartCards = [];
        
        selectedParts.each(function() {
            const partCard = $(this);
            const partId = partCard.data('part-id');
            const partType = partCard.data('part-type');
            
            // Check if this part type is already in the assembly
            if ($(`.aircraft-part.part-${partType}`).hasClass('filled')) {
                toastr.warning(`Bu montajda zaten bir ${partCard.find('span:first').text().trim()} parçası var.`);
                return true; // continue to next part
            }
            
            partIds.push(partId);
            selectedPartCards.push(partCard);
        });
        
        if (partIds.length === 0) {
            return; // No valid parts to add
        }
        
        // Add all parts in a single request
        $.ajax({
            url: `/assembly/api/processes/${assemblyId}/add_part/`,
            type: 'POST',
            data: JSON.stringify({ part_ids: partIds }),
            contentType: 'application/json',
            success: function(response) {
                if (response.added_parts && response.added_parts.length > 0) {
                    toastr.success(`${response.added_parts.length} parça başarıyla eklendi.`);
                    
                    // Remove the added parts from the UI
                    selectedPartCards.forEach(partCard => {
                        const partTypeContainer = partCard.closest('.part-type-container');
                        partCard.remove();
                        
                        if (partTypeContainer.children().length === 0) {
                            // If no more parts of this type, remove the entire section
                            partTypeContainer.closest('.part-type-section').remove();
                        }
                    });
                    
                    // Update the skeleton display and logs
                    updateSkeletonDisplay();
                    
                    // Check if we have all parts to complete assembly
                    checkCompletionEligibility();
                }
                
                // Display any errors
                if (response.errors && response.errors.length > 0) {
                    response.errors.forEach(error => {
                        toastr.error(`Hata (Parça #${error.part_id}): ${error.error || JSON.stringify(error.errors)}`);
                    });
                }
            },
            error: function(xhr) {
                let errorMsg = 'Parçalar eklenirken bir hata oluştu.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                toastr.error(errorMsg);
            }
        });
    });
    
    /**
     * Update the skeleton display based on current assembly parts
     */
    function updateSkeletonDisplay() {
        // Get current assembly status and parts
        $.ajax({
            url: `/assembly/api/processes/${assemblyId}/`,
            type: 'GET',
            success: function(assembly) {
                // Update assembly status
                updateAssemblyStatus(assembly);
                
                // Update header information
                updateHeaderInfo(assembly);
                
                // Mark parts as filled/unfilled without changing their position
                $('.aircraft-part').each(function() {
                    const partElement = $(this);
                    const partType = partElement.data('part-type');
                    const matchingPart = assembly.parts.find(p => p.part.part_type === partType);
                    
                    if (matchingPart) {
                        // Part exists in assembly - mark as filled
                        partElement.addClass('filled');
                        partElement.text(matchingPart.part.part_type_display);
                    } else {
                        // Part doesn't exist in assembly - mark as unfilled
                        partElement.removeClass('filled');
                        partElement.text('');
                    }
                });
                
                // Update completion button state
                checkCompletionEligibility(assembly.missing_parts);
                
                // Update logs
                updateAssemblyLogs(assembly.logs);
            },
            error: function(error) {
                toastr.error('Montaj durumu güncellenirken hata oluştu.');
                console.error('Error updating assembly:', error);
            }
        });
    }
    
    /**
     * Update the assembly status display
     */
    function updateAssemblyStatus(assembly) {
        const statusContainer = $('#assembly-status');
        statusContainer.removeClass().addClass(`assembly-status status-${assembly.status}`);
        
        // Get the status display text - use get_status_display or status_display
        let statusText = assembly.get_status_display;
        if (!statusText) {
            statusText = assembly.status_display;
        }
        statusContainer.text(`Durum: ${statusText}`);
        
        // Show/hide actions based on assembly status
        if (assembly.status !== 'in_progress') {
            $('.assembly-in-progress-actions').hide();
            if (assembly.status === 'completed' && assembly.aircraft) {
                $('#aircraft-completed-message').show();
                $('#completed-aircraft-id').text(assembly.aircraft);
            }
        } else {
            $('.assembly-in-progress-actions').show();
            $('#aircraft-completed-message').hide();
        }
    }
    
    /**
     * Check if all required parts are present for completion
     */
    function checkCompletionEligibility(missingParts) {
        const completeBtn = $('#complete-assembly-btn');
        
        if (!missingParts || missingParts.length === 0) {
            completeBtn.prop('disabled', false);
            $('#missing-parts-warning').hide();
        } else {
            completeBtn.prop('disabled', true);
            
            // Show missing parts warning
            let missingPartsList = '';
            missingParts.forEach(partType => {
                switch(partType) {
                    case 'wing': missingPartsList += 'Kanat, '; break;
                    case 'body': missingPartsList += 'Gövde, '; break;
                    case 'tail': missingPartsList += 'Kuyruk, '; break;
                    case 'avionics': missingPartsList += 'Aviyonik, '; break;
                }
            });
            
            missingPartsList = missingPartsList.slice(0, -2); // Remove trailing comma and space
            $('#missing-parts-list').text(missingPartsList);
            $('#missing-parts-warning').show();
        }
    }
    
    /**
     * Check if there are missing parts for the aircraft type
     */
    function checkMissingParts(availableParts) {
        const missingPartsAlert = $('#inventory-warning');
        const missingPartsList = $('#inventory-missing-parts');
        
        const missing = [];
        
        // Check each part type
        if (availableParts.wing === 0) missing.push('Kanat');
        if (availableParts.body === 0) missing.push('Gövde');
        if (availableParts.tail === 0) missing.push('Kuyruk');
        if (availableParts.avionics === 0) missing.push('Aviyonik');
        
        if (missing.length > 0) {
            missingPartsList.text(missing.join(', '));
            missingPartsAlert.show();
        } else {
            missingPartsAlert.hide();
        }
    }
    
    /**
     * Complete the assembly
     */
    $('#complete-assembly-btn').on('click', function() {
        if (confirm('Montajı tamamlamak istediğinize emin misiniz?')) {
            $.ajax({
                url: `/assembly/api/processes/${assemblyId}/complete_assembly/`,
                type: 'POST',
                success: function(response) {
                    toastr.success(response.message);
                    updateSkeletonDisplay();
                },
                error: function(xhr) {
                    let errorMsg = 'Montaj tamamlanırken bir hata oluştu.';
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        errorMsg = xhr.responseJSON.error;
                    }
                    toastr.error(errorMsg);
                }
            });
        }
    });
    
    /**
     * Remove a part from the assembly
     */
    $('.aircraft-part').on('click', function() {
        if (!$(this).hasClass('filled') || $('#assembly-status').hasClass('status-completed')) {
            return;
        }
        
        const partType = $(this).data('part-type');
        
        // Find the assembly part ID
        $.ajax({
            url: `/assembly/api/processes/${assemblyId}/`,
            type: 'GET',
            success: function(assembly) {
                const part = assembly.parts.find(p => p.part.part_type === partType);
                
                if (part) {
                    if (confirm(`Bu ${part.part.part_type_display} parçasını çıkarmak istediğinize emin misiniz?`)) {
                        // Remove the part
                        $.ajax({
                            url: `/assembly/api/processes/${assemblyId}/remove_part/`,
                            type: 'POST',
                            data: JSON.stringify({ part_id: part.part.id }),
                            contentType: 'application/json',
                            success: function() {
                                toastr.success('Parça başarıyla çıkarıldı.');
                                // Reload available parts and update skeleton
                                loadAvailableParts();
                                updateSkeletonDisplay();
                            },
                            error: function(xhr) {
                                let errorMsg = 'Parça çıkarılırken bir hata oluştu.';
                                if (xhr.responseJSON && xhr.responseJSON.error) {
                                    errorMsg = xhr.responseJSON.error;
                                }
                                toastr.error(errorMsg);
                            }
                        });
                    }
                }
            }
        });
    });
    
    /**
     * Cancel the assembly
     */
    $('#cancel-assembly-btn').on('click', function() {
        const reason = prompt('İptal etme nedeniniz nedir?', 'İptal edildi');
        
        if (reason !== null) {
            $.ajax({
                url: `/assembly/api/processes/${assemblyId}/cancel_assembly/`,
                type: 'POST',
                data: JSON.stringify({ reason: reason }),
                contentType: 'application/json',
                success: function(response) {
                    toastr.success(response.message);
                    
                    // Update the UI
                    updateSkeletonDisplay();
                    
                    // Reload available parts since they're back in the pool
                    loadAvailableParts();
                },
                error: function(xhr) {
                    let errorMsg = 'Montaj iptal edilirken bir hata oluştu.';
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        errorMsg = xhr.responseJSON.error;
                    }
                    toastr.error(errorMsg);
                }
            });
        }
    });
    
    /**
     * Update the assembly logs display
     */
    function updateAssemblyLogs(logs) {
        const logsContainer = $('.list-group-flush');
        logsContainer.empty();
        
        if (logs && logs.length > 0) {
            // Pagination configuration
            const logsPerPage = 5;
            const totalPages = Math.ceil(logs.length / logsPerPage);
            let currentPage = 1;
            
            // Function to display logs for current page
            const displayLogsForPage = (page) => {
                logsContainer.empty();
                const startIndex = (page - 1) * logsPerPage;
                const endIndex = Math.min(startIndex + logsPerPage, logs.length);
                
                // Display logs for current page
                for (let i = startIndex; i < endIndex; i++) {
                    const log = logs[i];
                    
                    // Format timestamp if it's in ISO format
                    let timestamp = log.timestamp;
                    if (typeof timestamp === 'string' && timestamp.includes('T')) {
                        const date = new Date(timestamp);
                        timestamp = formatDate(date);
                    }
                    
                    // Prepare part information if it exists
                    let partInfo = '';
                    if (log.part && log.part.part_type_display) {
                        partInfo = `<div><strong>Parça:</strong> ${log.part.part_type_display} (#${log.part.id})</div>`;
                    }
                    
                    // Prepare notes if they exist
                    let notesInfo = '';
                    if (log.notes) {
                        // Translate English part names in notes to Turkish
                        let translatedNotes = log.notes;
                        translatedNotes = translatedNotes.replace('Added Wing part', 'Kanat parçası eklendi');
                        translatedNotes = translatedNotes.replace('Added Body part', 'Gövde parçası eklendi');
                        translatedNotes = translatedNotes.replace('Added Tail part', 'Kuyruk parçası eklendi');
                        translatedNotes = translatedNotes.replace('Added Avionics part', 'Aviyonik parçası eklendi');
                        
                        notesInfo = `<div class="text-muted mt-1">${translatedNotes}</div>`;
                    }
                    
                    // Get username safely
                    let username = 'Bilinmeyen Kullanıcı';
                    if (log.action_by && log.action_by.username) {
                        username = log.action_by.username;
                    }
                    
                    const logItem = $(`
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <strong>${log.action_display}</strong>
                                <small class="text-muted">${timestamp}</small>
                            </div>
                            ${partInfo}
                            ${notesInfo}
                            <small><strong>İşlemi Yapan:</strong> ${username}</small>
                        </div>
                    `);
                    logsContainer.append(logItem);
                }
                
                // Add pagination controls if needed
                if (totalPages > 1) {
                    const paginationControls = $(`
                        <div class="pagination-container mt-3 d-flex justify-content-between align-items-center">
                            <div>
                                <small class="text-muted">Sayfa ${page}/${totalPages} (Toplam ${logs.length} kayıt)</small>
                            </div>
                            <div class="btn-group" role="group">
                                <button class="btn btn-sm btn-outline-secondary" id="prev-page" ${page === 1 ? 'disabled' : ''}>
                                    <i class="bi bi-chevron-left"></i> Önceki
                                </button>
                                <button class="btn btn-sm btn-outline-secondary" id="next-page" ${page === totalPages ? 'disabled' : ''}>
                                    Sonraki <i class="bi bi-chevron-right"></i>
                                </button>
                            </div>
                        </div>
                    `);
                    
                    logsContainer.append(paginationControls);
                    
                    // Add event listeners for pagination buttons
                    $('#prev-page').on('click', function() {
                        if (currentPage > 1) {
                            currentPage--;
                            displayLogsForPage(currentPage);
                        }
                    });
                    
                    $('#next-page').on('click', function() {
                        if (currentPage < totalPages) {
                            currentPage++;
                            displayLogsForPage(currentPage);
                        }
                    });
                }
            };
            
            // Initial display
            displayLogsForPage(currentPage);
            
        } else {
            logsContainer.append('<div class="list-group-item text-center">Henüz işlem kaydı yok.</div>');
        }
    }
    
    /**
     * Update the header information with latest user and date details
     */
    function updateHeaderInfo(assembly) {
        // Update the started by information
        if (assembly.started_by && assembly.started_by.username) {
            $('#baslatanRow span').text(assembly.started_by.username);
        }
        
        // Update the start date - format properly if it's in ISO format
        if (assembly.start_date) {
            let startDate = assembly.start_date;
            // Check if this is an ISO date string (contains T)
            if (typeof startDate === 'string' && startDate.includes('T')) {
                const date = new Date(startDate);
                startDate = formatDate(date);
            }
            $('#baslamaTarihiRow span').text(startDate);
        }
        
        // Update the last updated by information
        if (assembly.completed_by && assembly.completed_by.username) {
            $('#sonGuncelleyenRow span').text(assembly.completed_by.username);
        } else {
            $('#sonGuncelleyenRow span').text("Henüz güncellenmedi");
        }
        
        // Update the last updated date - format properly if it's in ISO format
        if (assembly.completion_date) {
            let completionDate = assembly.completion_date;
            // Check if this is an ISO date string (contains T)
            if (typeof completionDate === 'string' && completionDate.includes('T')) {
                const date = new Date(completionDate);
                completionDate = formatDate(date);
            }
            $('#sonGuncellemeTarihiRow span').text(completionDate);
        } else {
            $('#sonGuncellemeTarihiRow span').text("Henüz güncellenmedi");
        }
    }
    
    /**
     * Format date to DD.MM.YYYY HH:MM format
     */
    function formatDate(date) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${day}.${month}.${year} ${hours}:${minutes}`;
    }
}); 