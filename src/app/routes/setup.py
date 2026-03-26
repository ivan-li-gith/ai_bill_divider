from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.app.database import save_profile

setup = Blueprint('setup', __name__)

@setup.route('/setup')
def setup_page():
    if "user_id" not in session:
        return redirect(url_for('auth.login_page'))
        
    default_name = session.pop('oauth_name', '')
    default_email = session.pop('oauth_email', '')
    
    return render_template('setup.html', default_name=default_name, default_email=default_email)

@setup.route('/setup/save', methods=['POST'])
def save():
    user_id = session.get("user_id")
    display_name = request.form.get("display_name")
    email = request.form.get("email", "")
    
    try:
        save_profile(user_id, display_name, email)
        session["user_name"] = display_name
        flash(f"Profile created! Welcome to Split Em, {display_name}.", "success")
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        flash(f"An error occurred during setup: {e}", "danger")
        return redirect(url_for('setup.setup_page'))