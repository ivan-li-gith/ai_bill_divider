import pandas as pd
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from src.app.core.database import *

history = Blueprint('history', __name__)

@history.route('/history')
def index():
    if "user_id" not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_groups = get_user_groups
    group_id = request.args.get('group_id', type=int)
    
    if not group_id and user_groups:
        group_id = user_groups[0]['group_id']
    
    billing_history = load_history(user_id)
    
    if not billing_history.empty and group_id:
        names = get_group_members(group_id)
        month_displays = calculate_monthly_data(user_id, billing_history, names)
        month_displays.reverse() 
    else:
        month_displays = []

    return render_template('history.html', month_displays=month_displays, groups=user_groups, selected_group=group_id)

@history.route('/update_payment', methods=['POST'])
def update_payment():
    user_id = session['user_id']
    month = request.form.get('month')
    group_id = request.form.get('group_id', type=int)
    
    names = get_group_members(group_id)
    # Re-calculate names list to include owner for the split
    full_member_list = ["Me"] + [n for n in names if n != "Me"]
    
    updated_rows = []
    for name in full_member_list:
        is_paid = request.form.get(f"paid_{month}_{name}") == 'on'
        updated_rows.append({
            "Roommate Name": name,
            "Paid": is_paid,
            "Current Month Split": float(request.form.get(f"split_{month}_{name}")),
            "Rollover Amount": float(request.form.get(f"rollover_{month}_{name}")),
            "Total Owed": float(request.form.get(f"total_{month}_{name}"))
        })
    
    df = pd.DataFrame(updated_rows)
    save_tracker(user_id, df, month, group_id)
    
    flash(f"Updated payments for {month}", "success")
    return redirect(url_for('history.index', group_id=group_id))

@history.route('/clear_history', methods=['POST'])
def clear_history():
    if "user_id" not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    
    try:
        clear_db(user_id)
        flash("All billing and payment history has been cleared.", "success")
    except Exception as e:
        flash(f"Error clearing database: {e}", "danger")
        
    return redirect(url_for('history.history_page'))

def calculate_monthly_data(user_id, billing_history, names, group_id):
    # (Existing sorting logic remains the same)
    unique_months = billing_history["Billing Month"].unique()
    months_ascending = sorted(unique_months, key=lambda d: pd.to_datetime(d, format='%B %Y'))
    
    # Filter 'Me' out if already in names, then add to the start
    full_member_list = ["Me"] + [n for n in names if n != "Me"]
    running_rollover = {name: 0.0 for name in full_member_list}
    month_displays = []
    
    for month in months_ascending:
        month_df = billing_history[billing_history["Billing Month"] == month]
        monthly_total = month_df["Total Amount Due"].sum()
        num_ppl = len(full_member_list)
        monthly_split = round(monthly_total / num_ppl, 2) if num_ppl > 0 else 0
        
        # Now uses group-aware paid status
        paid_dict = get_paid_status(user_id, month, group_id)
        
        roommates = pd.DataFrame({
            "Roommate Name": full_member_list,
            "Current Month Split": monthly_split,
            "Rollover Amount": [running_rollover[name] for name in full_member_list],
            "Paid": [bool(paid_dict.get(name, False)) for name in full_member_list]
        })
        
        roommates["Total Owed"] = (roommates["Current Month Split"] + roommates["Rollover Amount"]).round(2)
        
        for idx, row in roommates.iterrows():
            running_rollover[row["Roommate Name"]] = 0.0 if row["Paid"] else row["Total Owed"]
        
        month_displays.append({
            "month": month,
            "df": month_df,
            "roommates": roommates,
            "monthly_total": monthly_total,
            "monthly_split": monthly_split,
            "group_id": group_id
        })
    return month_displays