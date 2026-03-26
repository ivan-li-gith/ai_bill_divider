// src/app/static/js/activity.js
document.addEventListener('DOMContentLoaded', function() {
    // --- Existing Checkbox Logic ---
    document.querySelectorAll('.paid-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const form = this.closest('form');
            const formData = new FormData(form);
            const month = this.dataset.month;
            const name = this.dataset.name;
            
            // Show loading spinner
            const statusIcon = document.getElementById(`status-${month}-${name}`);
            if (statusIcon) {
                statusIcon.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"></div>';
            }
            
            formData.append('target_name', name);

            fetch(form.action, { 
                method: 'POST', 
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest'}
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show success checkmark
                    if (statusIcon) {
                        statusIcon.innerHTML = '<span class="text-success fw-bold">✓</span>';
                        setTimeout(() => { statusIcon.innerHTML = ''; }, 2000);
                    }
                    
                    // Update the cascading totals on the page dynamically
                    for (const [monthName, roommates] of Object.entries(data.updates)) {
                        for (const [roommateName, values] of Object.entries(roommates)) {
                            const totalElement = document.getElementById(`total-owed-${monthName}-${roommateName}`);
                            if (totalElement) { totalElement.innerText = `$${values.total}`; }
                            
                            const rolloverInput = document.getElementById(`rollover-input-${monthName}-${roommateName}`);
                            if (rolloverInput) { rolloverInput.value = values.rollover; }
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error updating status:', error);
                if (statusIcon) {
                    statusIcon.innerHTML = '<span class="text-danger fw-bold">✗</span>';
                }
            });
        });
    });
});

// --- UI Toggle Functions ---

// Handles expanding and collapsing the ledger tables
function toggleSection(headerElement) {
    const content = headerElement.nextElementSibling;
    const icon = headerElement.querySelector('.caret-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        icon.style.transform = 'rotate(0deg)';
    }
}

// --- MISSING JS REMOVED: openUnifiedModal is no longer needed ---

// Adds a new blank row to the AI receipt staging modal
function addReceiptItemRow() {
    const tbody = document.getElementById('receiptItemsBody');
    const countInput = document.getElementById('receiptItemCount');
    const currentIndex = parseInt(countInput.value);
    
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td style="padding: 4px;">
            <input type="text" name="name_${currentIndex}" placeholder="New Item" required style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px;">
        </td>
        <td style="padding: 4px;">
            <input type="number" step="0.01" name="amount_${currentIndex}" placeholder="0.00" required style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px;">
        </td>
    `;
    tbody.appendChild(tr);
    countInput.value = currentIndex + 1;
}

// Shows loading state when saving staged utility bills
function handleSaveHistory(event) {
    const btn = event.target.querySelector('button[type="submit"]');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = 'Saving...';
    }
}