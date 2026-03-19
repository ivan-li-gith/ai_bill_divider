from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.app.core.supabase_client import supabase
from src.app.core.database import get_profile

auth = Blueprint('auth', __name__)

@auth.route('/')
def index():
    if "user_id" in session:
        return redirect(url_for('home.index'))
    
    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            
            if response:
                session["user_id"] = response.user.id
                profile = get_profile(response.user.id)
                
                if not profile:
                    return redirect(url_for("setup.index")) 
                return redirect(url_for("home.index"))
        except Exception as e:
            flash(f"Login failed: {str(e)}", "danger")
            
    return render_template('login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        
        try:
            response = supabase.auth.sign_up({"email": email, "password": password})
            flash("Check your email for a confirmation link!", "info")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"Signup failed: {str(e)}", "danger")
            
    return render_template('signup.html')

@auth.route('/login/<provider>')
def oauth_login(provider):
    try:
        redirect_url = url_for("auth.oauth_callback", _external=True)
        response = supabase.auth.sign_in_with_oauth({
            "provider": provider, 
            "options": {
                "redirect_to": redirect_url
            }    
        })
        
        return redirect(response.url)
    except Exception as e:
        return f"OAuth sign in failed: {e}"
    
@auth.route('/callback')
def oauth_callback():
    code = request.args.get("code")
    if code:
        try:
            response = supabase.auth.exchange_code_for_session({"auth_code": code})
            session["user_id"] = response.user.id
            session["user_name"] = response.user.email
            
            flash("Successfully authenticated with Google!", "success")
            return redirect(url_for("setup.index"))
        except Exception as e:
            flash(f"Authentication error: {e}", "danger")
            return redirect(url_for("auth.login"))
        
    return "Missing authorization code", 400

@auth.route('/logout')
def logout():
    supabase.auth.sign_out()
    session.clear()
    return redirect(url_for('auth.login'))