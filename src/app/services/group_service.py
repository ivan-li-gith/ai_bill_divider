import json
from src.app.database import (
    get_user_groups, create_group, add_group_member, 
    get_group_members, update_group_name, update_and_sync_member
)

def fetch_user_groups(user_id):
    """Fetches groups and ensures the members JSON is properly parsed for the frontend."""
    user_groups = get_user_groups(user_id)
    for group in user_groups:
        members_data = group.get('members_json')
        if isinstance(members_data, str):
            try:
                group['members'] = json.loads(members_data)
            except json.JSONDecodeError:
                group['members'] = []
        else:
            group['members'] = members_data or []
    return user_groups

def add_new_group(user_id, group_name, group_type, names, emails):
    """Handles the creation of a new group or individual card."""
    if group_type == 'individual' and names:
        group_name = names[0]
        
    if not group_name:
        raise ValueError("Group name is required.")
        
    group_id = create_group(user_id, group_name, group_type)
    _process_members(user_id, group_id, names, emails, auto_create_individual=(group_type == 'group'))
    return group_name

def modify_group(user_id, group_id, group_type, new_name, existing_data, new_data):
    """Handles the complex logic of updating both full groups and individual cards."""
    # SCENARIO A: Editing an Individual Card
    if group_type == 'individual':
        # FIX: Changed new_data to existing_data
        names, emails = existing_data['names'], existing_data['emails']
        if names:
            clean_name = names[0].strip()
            clean_email = emails[0].strip() if emails else ""
            
            if clean_name:
                members = get_group_members(group_id)
                target = next((m for m in members if m['role'] != 'owner'), None)
                if target:
                    update_and_sync_member(target['group_member_id'], user_id, clean_name, clean_email)
                    
    # SCENARIO B: Editing a Full Group
    else:
        if new_name:
            update_group_name(group_id, new_name)
            
            # 1. Update existing members
            for m_id, name, email in zip(existing_data['ids'], existing_data['names'], existing_data['emails']):
                clean_name = name.strip()
                if clean_name:
                    update_and_sync_member(m_id, user_id, clean_name, email.strip())
                    
            # 2. Add any brand new members
            _process_members(user_id, group_id, new_data['names'], new_data['emails'], auto_create_individual=True)

def _process_members(user_id, group_id, names, emails, auto_create_individual=False):
    """Private helper to iterate through form lists and save members."""
    for name, email in zip(names, emails): 
        clean_name = name.strip()
        clean_email = email.strip() if email else ""
        
        if clean_name:
            add_group_member(group_id, clean_name, clean_email) 
            if auto_create_individual:
                _ensure_individual_exists(user_id, clean_name, clean_email)

def _ensure_individual_exists(owner_id, name, email):
    """Private helper to prevent empty-email collisions by falling back to name checks."""
    clean_name = name.strip()
    clean_email = email.strip() if email else ""
    existing_groups = get_user_groups(owner_id)
    
    for group in existing_groups:
        if group.get('group_type') == 'individual':
            members = group.get('members_json', [])
            if isinstance(members, str):
                members = json.loads(members)
            
            for m in members:
                if m.get('role') == 'owner': 
                    continue
                if (clean_email and m.get('email') == clean_email) or (not clean_email and m.get('name') == clean_name):
                    return # They already exist!

    new_id = create_group(owner_id, clean_name, 'individual')
    add_group_member(new_id, clean_name, clean_email)