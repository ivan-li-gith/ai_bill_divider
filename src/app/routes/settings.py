from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.app.database import get_profile, save_profile

settings = Blueprint('settings', __name__)

@settings.route('/settings', methods=['GET', 'POST'])
def index():
    if "user_id" not in session:
        return redirect(url_for('auth.login_page'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        name = request.form.get('display_name')
        email = request.form.get('email', '')
        # phone removal
        
        try:
            save_profile(user_id, name, email)
            session['user_name'] = name
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating profile: {e}', 'danger')
            
        return redirect(url_for('settings.index'))
        
    profile = get_profile(user_id)
    return render_template('settings.html', profile=profile)