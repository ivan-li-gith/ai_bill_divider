from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from src.app.database import delete_group, delete_member
from src.app.services.group_service import fetch_user_groups, add_new_group, modify_group

groups = Blueprint('groups', __name__)

@groups.route('/groups')
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))
    
    user_groups = fetch_user_groups(session["user_id"])
    return render_template('groups.html', groups=user_groups)

@groups.route('/groups/create', methods=['POST'])
def create():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))
    
    try:
        group_name = add_new_group(
            user_id=session["user_id"],
            group_name=request.form.get('group_name'),
            group_type=request.form.get('group_type', 'group'),
            names=request.form.getlist('new_names[]'),
            emails=request.form.getlist('new_emails[]')
        )
        flash(f"Group '{group_name}' created successfully!", "success")
    except Exception as e:
        flash(f"Error creating group: {e}", "danger")
            
    return redirect(url_for('groups.index'))

@groups.route('/groups/edit/<int:group_id>', methods=['POST'])
def edit(group_id):
    if "user_id" not in session: 
        return redirect(url_for("auth.login_page"))
    
    existing_data = {
        'ids': request.form.getlist('existing_ids[]'),
        'names': request.form.getlist('existing_names[]'),
        'emails': request.form.getlist('existing_emails[]')
    }
    
    new_data = {
        'names': request.form.getlist('new_names[]'),
        'emails': request.form.getlist('new_emails[]')
    }
    
    try:
        modify_group(
            user_id=session["user_id"],
            group_id=group_id,
            group_type=request.form.get('group_type', 'group'),
            new_name=request.form.get('group_name'),
            existing_data=existing_data,
            new_data=new_data
        )
        flash("Updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating: {e}", "danger")
        
    return redirect(url_for('groups.index'))

@groups.route('/groups/delete/<int:group_id>', methods=['POST'])
def delete(group_id):
    if "user_id" in session:
        delete_group(group_id, session["user_id"])
        flash("Group deleted.", "info")
    return redirect(url_for('groups.index'))

@groups.route('/groups/members/delete/<int:member_id>', methods=['POST'])
def remove_member(member_id):
    if "user_id" not in session:
        return "Unauthorized", 401
    
    try:
        delete_member(member_id)
        return "Success", 200
    except Exception as e:
        return str(e), 500