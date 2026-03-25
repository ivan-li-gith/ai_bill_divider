from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from src.app.database import get_user_groups, load_history, get_group_members, get_unpaid_expense_splits, get_subscription
from src.app.routes.utilities import calculate_utilities, get_member_names
from src.app.core.notifications import generate_pdf_breakdown, send_email_with_pdf
from datetime import datetime

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))
    
    user_id = session["user_id"]
    user_groups = get_user_groups(user_id)
    
    # Default to 0 (ALL) if no filter is applied
    group_id = request.args.get('group_id', type=int)
    if group_id is None:
        group_id = 0
        
    # Dictionary to aggregate debts across all groups and categories
    debtors_dict = {}
    
    import json
    contact_map = {}
    for g in user_groups:
        members = g.get('members_json', [])
        if isinstance(members, str): members = json.loads(members)
        for m in (members or []):
            if m.get('name') not in contact_map:
                contact_map[m.get('name')] = {'email': m.get('email', ''), 'phone': m.get('phone', '')}

    def add_debt(name, category, amount):
        if amount <= 0: return
        if name not in debtors_dict:
            contact = contact_map.get(name, {})
            debtors_dict[name] = {
                'name': name, 'utilities': 0.0, 'expenses': 0.0, 'subscriptions': 0.0, 'total': 0.0,
                'email': contact.get('email', ''), 'phone': contact.get('phone', '') # NEW
            }
        debtors_dict[name][category] += amount
        debtors_dict[name]['total'] += amount
            
    # Determine which groups to pull data for
    groups_to_check = [group_id] if group_id != 0 else [g['group_id'] for g in user_groups]
    
    for gid in groups_to_check:
        # 1. Tally Utility Debts (Latest Rollover Amount)
        billing_history = load_history(user_id, gid)
        if not billing_history.empty:
            members = get_group_members(gid)
            names = get_member_names(user_id, members)
            month_displays = calculate_utilities(user_id, billing_history, names, gid)
            
            if month_displays:
                latest_month = month_displays[-1]["roommates"]
                for _, row in latest_month.iterrows():
                    name = row["Roommate Name"]
                    if name != "Me" and not row["Paid"] and row["Total Owed"] > 0:
                        add_debt(name, 'utilities', row["Total Owed"])
                        
        # 2. Tally One-Off Expense Debts
        unpaid_exps = get_unpaid_expense_splits(gid)
        for name, amt in unpaid_exps.items():
            if name != "Me":
                add_debt(name, 'expenses', amt)
                
        # 3. Subscriptions (Logic placeholder for when subscription tracking is added)
        subs = get_subscription(user_id, gid)
        if subs:
            current_day = datetime.today().day
            members = get_group_members(gid)
            num_people = len(members)
            
            if num_people > 0:
                for sub in subs:
                    # Only charge them if the billing day has passed for this month
                    if current_day >= sub['billing_day']:
                        # Divide the cost evenly among all members
                        split_amt = round(float(sub['amount']) / num_people, 2)
                        
                        for m in members:
                            # Assign the debt to everyone except the owner
                            if m.get('role') != 'owner':
                                add_debt(m['member_name'], 'subscriptions', split_amt)
        
    # Convert dict to list for the template
    debtors = list(debtors_dict.values())
    total_uncollected = sum(d['total'] for d in debtors)
            
    return render_template('dashboard.html', 
                           debtors=debtors,
                           total_uncollected=total_uncollected,
                           groups=user_groups, 
                           selected_group_id=group_id)
    
@dashboard.route('/dashboard/notify', methods=['POST'])
def send_notification():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))

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