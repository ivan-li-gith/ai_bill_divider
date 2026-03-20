import pandas as pd
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from src.app.core.parser import extract_from_pdf, get_bill_details
from src.app.database import get_user_groups, save_bill_history, load_history, get_group_members, save_tracker, get_paid_status

utilities = Blueprint('utilities', __name__)

def get_member_names(user_id, members):
    return ["Me" if str(m.get("user_id")) == str(user_id) else m["member_name"] for m in members]

@utilities.route('/utilities')
def index():
    if "user_id" not in session:
        return redirect(url_for('auth.login_page'))
    
    user_id = session["user_id"]
    user_groups = get_user_groups(user_id)
    group_id = request.args.get('group_id', type=int) or (user_groups[0]['group_id'] if user_groups else None)
    
    month_displays = []
    if group_id:
        billing_history = load_history(user_id, group_id)
        
        if not billing_history.empty:
            members = get_group_members(group_id)
            names = get_member_names(user_id, members)
            month_displays = calculate_utilities(user_id, billing_history, names, group_id)
            month_displays.reverse() 

    return render_template('utilities.html', month_displays=month_displays, groups=user_groups, selected_group_id=group_id)
    
@utilities.route('/utilities/upload', methods=['POST'])
def upload():
    group_id = request.form.get("group_id")
    files = request.files.getlist('bills')
    all_bill_data = []
    
    for file in files:
        if file.filename.endswith('.pdf'):
            try:
                extracted_text = extract_from_pdf(file)
                bill_data = get_bill_details(extracted_text)
                all_bill_data.append(bill_data)
            except Exception as e:
                flash(f"Failed to process {file.filename}: {e}", "danger")

    session['staged_bills'] = all_bill_data
    session['staged_group_id'] = group_id
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success"})
    return redirect(url_for('utilities.index', group_id=group_id))

@utilities.route('/utilities/save', methods=['POST'])
def save():
    user_id = session['user_id']
    group_id = session.get('staged_group_id')
    bill_count = int(request.form.get('bill_count', 0))
    corrected_data = []

    for i in range(bill_count):
        month = request.form.get(f"month_{i}")
        if month in ["Unknown", "Error", ""]:
            flash(f"Row {i+1} has an invalid month. Please correct it before saving.", "danger")
            return redirect(url_for('utilities.index', group_id=group_id))
        
        corrected_data.append({
            "Billing Month": request.form.get(f"month_{i}"),
            "Service Name": request.form.get(f"service_{i}"),
            "Service Period": request.form.get(f"period_{i}"),
            "Total Amount Due": float(request.form.get(f"amount_{i}", 0)),
            "group_id": group_id
        })

    if corrected_data:
        df = pd.DataFrame(corrected_data)
        save_bill_history(user_id, df)
        session.pop('staged_bills', None) 
        session.pop('staged_group_id', None)
        flash("Bills successfully saved to database!", "success")
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success"})
    
    return redirect(url_for('utilities.index', group_id=group_id))

@utilities.route('/utilities/update_status', methods=['POST'])
def update_status():
    user_id = session['user_id']
    month = request.form.get('month')
    group_id = request.form.get('group_id', type=int)
    
    members = get_group_members(group_id)
    names = get_member_names(user_id, members)
    
    updated_rows = []    
    for name in names:
        is_paid = request.form.get(f"paid_{month}_{name}") == 'on'
        split_val = float(request.form.get(f"split_{month}_{name}", 0))
        rollover_val = float(request.form.get(f"rollover_{month}_{name}", 0))
        total_val = round(split_val + rollover_val, 2)

        updated_rows.append({
            "Roommate Name": name,
            "Paid": is_paid,
            "Current Month Split": split_val,
            "Rollover Amount": rollover_val,
            "Total Owed": total_val
        })
        
    df = pd.DataFrame(updated_rows)
    save_tracker(user_id, df, month, group_id)
    billing_history = load_history(user_id, group_id)
    updated_months = calculate_utilities(user_id, billing_history, names, group_id)
    
    all_updates = {}
    for m in updated_months:
        month_name = m['month']
        all_updates[month_name] = {
            row['Roommate Name']: {
                "total": f"{row['Total Owed']:.2f}",
                "rollover": f"{row['Rollover Amount']:.2f}"
            }
            for _, row in m['roommates'].iterrows()
        }
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "status": "success", 
            "updates": all_updates
        })
    
    return redirect(url_for('utilities.index', group_id=group_id))

def calculate_utilities(user_id, billing_history, names, group_id):
    unique_months = billing_history["Billing Month"].unique()
    months_ascending = sorted(unique_months, key=lambda d: pd.to_datetime(d, format='%B %Y'))
    running_rollover = {name: 0.0 for name in names}
    month_displays = []

    for month in months_ascending:
        month_df = billing_history[billing_history["Billing Month"] == month]
        monthly_total = month_df["Total Amount Due"].sum()
        num_ppl = len(names)
        monthly_split = round(monthly_total / num_ppl, 2) if num_ppl > 0 else 0
        paid_dict = get_paid_status(user_id, month, group_id)
        
        roommates = pd.DataFrame({
            "Roommate Name": names,
            "Current Month Split": monthly_split,
            "Rollover Amount": [running_rollover[name] for name in names],
            "Paid": [bool(paid_dict.get(name, False)) for name in names]
        })
        
        roommates["Total Owed"] = (roommates["Current Month Split"] + roommates["Rollover Amount"]).round(2)
        
        for _, row in roommates.iterrows():
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
