from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.app.core.database import save_profile, create_group

setup = Blueprint('setup', __name__)

@setup.route('/setup')
def index():
    if "user_id" in session:
        return redirect(url_for('auth.login'))
    return render_template('setup.html')

@setup.route('/setup/save', methods=['POST'])
def save():
    user_id = session.get("user_id")
    display_name = request.form.get("display_name")
    age = request.form.get("age")
    group_name = request.form.get("group_name")
    
    try:
        save_profile(user_id, display_name, age)
        session["user_name"] = display_name
        
        if group_name:
            group_id = create_group(user_id, group_name)
            session["active_group_id"] = group_id
            session["active_group_name"] = group_name
            flash(f"Welcome, {display_name}! Your group '{group_name}' is ready.", "success")
        else:
            flash(f"Profile created! Welcome, {display_name}.", "success")
            
        return redirect(url_for('home.index'))
        
    except Exception as e:
        flash(f"An error occurred during setup: {e}", "danger")
        return redirect(url_for('setup.index'))
