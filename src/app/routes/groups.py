from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from src.app.core.database import *

groups = Blueprint('groups', __name__)

@groups.route('/groups')
def group_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user_groups = get_user_groups(session["user_id"])
    return render_template('groups.html', groups=user_groups)

@groups.route('/groups/create', methods=['POST'])
def create_group():
    group_name = request.form.get('group_name')
    if group_name:
        create_group(session["user_id"], group_name)
        flash(f"Group '{group_name}' created!", "success")
    return redirect(url_for('groups.index'))

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

