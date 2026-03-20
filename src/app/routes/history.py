import pandas as pd
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from src.app.database import get_user_groups, load_history, get_group_members, save_tracker, get_paid_status, clear_db

history = Blueprint('history', __name__)

@history.route('/history')
def history_page():
    if "user_id" not in session:
        return redirect(url_for('auth.login_page'))
    
    user_id = session['user_id']
    user_groups = get_user_groups(user_id)
    
    # Get group_id from URL, but DO NOT default it to the first group automatically
    group_id = request.args.get('group_id', type=int)
    
    month_displays = []
    if group_id:
        # Pass group_id to SQL to ensure we only get that group's bills
        billing_history = load_history(user_id, group_id)
        
        if not billing_history.empty:
            names = get_group_members(group_id)
            # Ensure group_id is passed to the calculator
            month_displays = calculate_monthly_data(user_id, billing_history, names, group_id)
            month_displays.reverse() 

    # Use 'selected_group_id' to match the template's expectations
    return render_template('history.html', 
                           month_displays=month_displays, 
                           groups=user_groups, 
                           selected_group_id=group_id)

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
    return redirect(url_for('history.history_page', group_id=group_id))

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
    group_history = billing_history[billing_history["group_id"] == group_id]
    unique_months = group_history["Billing Month"].unique()
    months_ascending = sorted(unique_months, key=lambda d: pd.to_datetime(d, format='%B %Y'))
    
    full_member_list = []
    for m in names:
        # Check if the member's user_id matches the logged-in user
        if m.get("user_id") == user_id:
            full_member_list.append("Me")
        else:
            full_member_list.append(m["member_name"])
    

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