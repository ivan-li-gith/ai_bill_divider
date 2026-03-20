import pandas as pd
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from src.app.core.parser import extract_from_pdf, get_bill_details
from src.app.database import get_user_groups, save_bill_history

bills = Blueprint('bills', __name__)

@bills.route('/bills', methods=['GET', 'POST'])
def bills_page():
    if "user_id" not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session["user_id"]
    groups = get_user_groups(user_id)
    return render_template('bills.html', groups=groups)

@bills.route('/upload_bills', methods=['POST'])
def upload_bills():
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
    return redirect(url_for('bills.bills_page'))

@bills.route('/confirm_bills', methods=['POST'])
def confirm_bills():
    if "user_id" not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    group_id = session.get('staged_group_id')
    bill_count = int(request.form.get('bill_count', 0))
    corrected_data = []

    for i in range(bill_count):
        month = request.form.get(f"month_{i}")
        
        # reject save if fields are still unknown
        if month in ["Unknown", "Error", ""]:
            flash(f"Row {i+1} has an invalid month. Please correct it before saving.", "danger")
            return redirect(url_for('bills.bills_page'))
        
        bill = {
            "Billing Month": request.form.get(f"month_{i}"),
            "Service Name": request.form.get(f"service_{i}"),
            "Service Period": request.form.get(f"period_{i}"),
            "Total Amount Due": float(request.form.get(f"amount_{i}", 0)),
            "group_id": group_id
        }
        corrected_data.append(bill)

    if corrected_data:
        df = pd.DataFrame(corrected_data)
        save_bill_history(user_id, df)
        group_id = session.get('staged_group_id')
        session.pop('staged_bills', None)   # clear session once saved
        session.pop('staged_group_id', None)
        flash("Bills successfully saved to database!", "success")
        return redirect(url_for('history.history_page', group_id=group_id))
    
    return redirect(url_for('bills.bills_page'))
