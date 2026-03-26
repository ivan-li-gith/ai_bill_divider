from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from src.app.core.notifications import generate_pdf_breakdown, send_email_with_pdf
from src.app.services.dashboard_service import get_dashboard_metrics

dashboard = Blueprint('dashboard', __name__)

# renders the dashboard with all expense history
@dashboard.route('/dashboard')
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user_id = session["user_id"]
    group_id = request.args.get('group_id', 0, type=int)
    debtors, total_uncollected, user_groups, my_expenses_total = get_dashboard_metrics(user_id, group_id)
            
    return render_template('dashboard.html', debtors=debtors, total_uncollected=total_uncollected, groups=user_groups, selected_group_id=group_id, my_expenses_total=my_expenses_total)

# generates pdf and sends it via email to notify user
@dashboard.route('/dashboard/notify', methods=['POST'])
def send_notification():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    name = request.form.get('name')
    total = float(request.form.get('total', 0))
    util = float(request.form.get('utilities', 0))
    exp = float(request.form.get('expenses', 0))
    sub = float(request.form.get('subscriptions', 0))
    method = request.form.get('method')
    
    try:
        if method == 'email':
            email = request.form.get('email')
            if not email:
                flash("Email address is required.", "danger")
                return redirect(url_for('dashboard.index'))
                
            pdf_bytes = generate_pdf_breakdown(name, total, util, exp, sub)
            send_email_with_pdf(email, name, pdf_bytes)
            flash(f"Breakdown PDF emailed to {name} at {email}!", "success")
    except Exception as e:
        flash(f"Failed to send notification: {str(e)}", "danger")
        
    return redirect(url_for('dashboard.index'))