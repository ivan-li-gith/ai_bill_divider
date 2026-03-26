document.addEventListener('DOMContentLoaded', function() {
    
    // --- UTILITY: Generate a Member Row HTML String ---
    function createMemberRow(isExisting = false, id = '', name = '', email = '', role = 'member') {
        const prefix = isExisting ? 'existing' : 'new';
        const disabledAttr = role === 'owner' ? 'readonly' : '';
        const idInput = isExisting ? `<input type="hidden" name="existing_ids[]" value="${id}">` : '';
        
        // Remove button is only available for non-owners
        const removeBtn = role !== 'owner' 
            ? `<button type="button" class="btn btn-outline-danger w-100" onclick="this.closest('.row').remove()">X</button>`
            : `<div class="text-muted small mt-2 text-center">Owner</div>`;

        return `
            <div class="row align-items-center mb-2 member-row">
                ${idInput}
                <div class="col-md-5 mb-2 mb-md-0">
                    <input type="text" class="form-control form-control-sm" name="${prefix}_names[]" placeholder="Name" value="${name}" required ${disabledAttr}>
                </div>
                <div class="col-md-5 mb-2 mb-md-0">
                    <input type="email" class="form-control form-control-sm" name="${prefix}_emails[]" placeholder="Email (Optional)" value="${email}" ${disabledAttr}>
                </div>
                <div class="col-md-2">
                    ${removeBtn}
                </div>
            </div>
        `;
    }

    // --- ADD MODAL LOGIC ---
    const addModal = document.getElementById('addGroupModal');
    if (addModal) {
        addModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const type = button.getAttribute('data-type'); // 'group' or 'individual'
            
            document.getElementById('add-group-type').value = type;
            const title = document.getElementById('addGroupModalLabel');
            const nameContainer = document.getElementById('add-group-name-container');
            const nameInput = document.getElementById('add-group-name');
            const membersContainer = document.getElementById('add-members-container');
            const addRowBtn = document.getElementById('btn-add-member-row');

            // Reset form
            membersContainer.innerHTML = '';
            
            if (type === 'individual') {
                title.textContent = 'Add Individual';
                nameContainer.style.display = 'none';
                nameInput.removeAttribute('required');
                addRowBtn.style.display = 'none'; // Only allow 1 row for individuals
                
                // Add exactly one blank row
                membersContainer.innerHTML = createMemberRow(false);
            } else {
                title.textContent = 'Create Group';
                nameContainer.style.display = 'block';
                nameInput.setAttribute('required', 'required');
                addRowBtn.style.display = 'block';
                
                // Add two blank rows to start a group
                membersContainer.innerHTML = createMemberRow(false) + createMemberRow(false);
            }
        });

        document.getElementById('btn-add-member-row').addEventListener('click', function() {
            document.getElementById('add-members-container').insertAdjacentHTML('beforeend', createMemberRow(false));
        });
    }

    // --- EDIT MODAL LOGIC ---
    const editModal = document.getElementById('editGroupModal');
    if (editModal) {
        editModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            
            // 1. Extract Data
            const groupId = button.getAttribute('data-group-id');
            const groupName = button.getAttribute('data-group-name');
            const groupType = button.getAttribute('data-group-type');
            const membersData = JSON.parse(button.getAttribute('data-members') || '[]');
            
            // 2. Setup Form & Basic Inputs
            document.getElementById('edit-group-form').action = `/groups/edit/${groupId}`;
            document.getElementById('edit-group-type').value = groupType;
            
            const nameContainer = document.getElementById('edit-group-name-container');
            const nameInput = document.getElementById('edit-group-name');
            const addRowBtn = document.getElementById('btn-edit-add-row');
            const newMembersTitle = document.getElementById('edit-new-members-title');

            if (groupType === 'individual') {
                nameContainer.style.display = 'none';
                addRowBtn.style.display = 'none';
                newMembersTitle.style.display = 'none';
            } else {
                nameContainer.style.display = 'block';
                nameInput.value = groupName;
                addRowBtn.style.display = 'inline-block';
                newMembersTitle.style.display = 'block';
            }

            // 3. Populate Existing Members
            const existingContainer = document.getElementById('edit-existing-members-container');
            existingContainer.innerHTML = '';
            
            membersData.forEach(member => {
                // If it's an individual, we hide the owner row because an individual card is just 1 person
                if (groupType === 'individual' && member.role === 'owner') return;
                
                existingContainer.insertAdjacentHTML('beforeend', createMemberRow(
                    true, member.id, member.name, member.email, member.role
                ));
            });

            // 4. Clear New Members Container
            document.getElementById('edit-new-members-container').innerHTML = '';
        });

        document.getElementById('btn-edit-add-row').addEventListener('click', function() {
            document.getElementById('edit-new-members-container').insertAdjacentHTML('beforeend', createMemberRow(false));
        });
    }
});