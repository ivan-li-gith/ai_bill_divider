import json
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from src.app.core.database import *

groups = Blueprint('groups', __name__)

@groups.route('/groups')
def group_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user_groups = get_user_groups(session["user_id"])
    
    # Parse the members JSON string into a usable Python list for the template
    for group in user_groups:
        if group.get('members_json'):
            try:
                # Handle stringified JSON from database
                members = json.loads(group['members_json']) if isinstance(group['members_json'], str) else group['members_json']
                group['members'] = members
            except:
                group['members'] = []
        else:
            group['members'] = []
            
    return render_template('groups.html', groups=user_groups)

@groups.route('/groups/create', methods=['POST'])
def create():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user_id = session["user_id"]
    group_name = request.form.get('group_name')
    names = request.form.getlist('new_names[]')
    emails = request.form.getlist('new_emails[]')
    
    if group_name:
        try:
            group_id = create_group(user_id, group_name)
            
            # Changed the IF statement below so email is truly optional
            for name, email in zip(names, emails):
                if name.strip(): 
                    add_group_member(group_id, name.strip(), email.strip())
            
            flash(f"Group '{group_name}' created successfully!", "success")
        except Exception as e:
            flash(f"Error creating group: {e}", "danger")
            
    return redirect(url_for('groups.group_page'))

@groups.route('/groups/<int:group_id>')
def details(group_id):
    members = get_group_members(group_id)
    # You might want to store which group is currently viewed in the session
    session["active_group_id"] = group_id 
    return render_template('group_details.html', members=members, group_id=group_id)

@groups.route('/groups/<int:group_id>/add_member', methods=['POST'])
def add_member(group_id):
    email = request.form.get('email')
    target_user_id = get_user_by_email(email)
    
    if target_user_id:
        add_group_member(group_id, target_user_id)
        flash(f"Added {email} to the group!", "success")
    else:
        flash("User not found. They must sign up for Split Em first.", "danger")
        
    return redirect(url_for('groups.details', group_id=group_id))

@groups.route('/groups/delete/<int:group_id>', methods=['POST'])
def delete(group_id):
    if "user_id" in session:
        delete_group(group_id, session["user_id"])
        flash("Group deleted.", "info")
    return redirect(url_for('groups.group_page'))

@groups.route('/groups/edit/<int:group_id>', methods=['POST'])
def edit(group_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    new_name = request.form.get('group_name')
    
    # Existing members to update
    existing_ids = request.form.getlist('existing_ids[]')
    existing_names = request.form.getlist('existing_names[]')
    existing_emails = request.form.getlist('existing_emails[]')
    
    # New members to add
    new_names = request.form.getlist('new_names[]')
    new_emails = request.form.getlist('new_emails[]')
    
    if new_name:
        try:
            update_group_name(group_id, new_name)
            
            # Update existing members
            for m_id, name, email in zip(existing_ids, existing_names, existing_emails):
                if name.strip():
                    update_member(m_id, name.strip(), email.strip())
            
            # Add new members
            for name, email in zip(new_names, new_emails):
                if name.strip():
                    add_group_member(group_id, name.strip(), email.strip())
            
            flash(f"Group '{new_name}' updated successfully!", "success")
        except Exception as e:
            flash(f"Error updating group: {e}", "danger")
            
    return redirect(url_for('groups.group_page'))

# src/app/routes/groups.py

@groups.route('/groups/members/delete/<int:member_id>', methods=['POST'])
def remove_member(member_id):
    if "user_id" not in session:
        return "Unauthorized", 401
    
    try:
        delete_member(member_id)
        return "Success", 200
    except Exception as e:
        return str(e), 500