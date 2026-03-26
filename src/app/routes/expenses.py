from flask import Blueprint, request, session, redirect, url_for, flash
from src.app.core.parser import extract_from_receipt_image
from src.app.database import add_expense, delete_expense
from datetime import datetime

expenses = Blueprint('expenses', __name__)

# processes receipt images and lets users review it
@expenses.route('/expenses/upload_receipt', methods=['POST'])
def upload_receipt():
    group_id = request.form.get("group_id")
    if not group_id or group_id == "0" or group_id == "None":
        group_id = None
    else:
        group_id = int(group_id)
        
    file = request.files.get('receipt_image')
    
    if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.heic')):
        try:
            items_list = extract_from_receipt_image(file)
            session['staged_receipt_items'] = items_list
            session['staged_expense_group'] = group_id
            flash("Receipt parsed successfully! Please review the items below.", "success")
        except Exception as e:
            flash(f"Failed to process receipt: {e}", "danger")
            
    return redirect(url_for('activity.index'))

# allows for manual entry
@expenses.route('/expenses/manual_add', methods=['POST'])
def manual_add():
    if "user_id" not in session: 
        return redirect(url_for('auth.login'))

    user_id = session["user_id"]
    group_id = request.form.get("group_id")
    if not group_id or group_id == "0" or group_id == "None":
        group_id = None
    else:
        group_id = int(group_id)
        
    item_name = request.form.get("item_name")
    amount = float(request.form.get("amount", 0))
    date = request.form.get("date") 
    payer_id = user_id 
    split_method = "even"

    if item_name and amount > 0:
        try:
            add_expense(group_id, user_id, date, item_name, amount, payer_id, split_method)
            flash(f"'{item_name}' added to ledger.", "success")
        except Exception as e:
            flash(f"Error saving expense: {e}", "danger")
            
    return redirect(url_for('activity.index', group_id=group_id or 0))

@expenses.route('/expenses/delete/<int:expense_id>', methods=['POST'])
def delete(expense_id):
    if "user_id" not in session:
        return redirect(url_for('auth.login'))
        
    try:
        delete_expense(expense_id)
        flash("Expense deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting expense: {e}", "danger")
        
    return redirect(url_for('activity.index'))

# saves all reviewed items 
@expenses.route('/expenses/save_staged', methods=['POST'])
def save_staged():
    if "user_id" not in session: 
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    group_id = session.get('staged_expense_group')
    if str(group_id) == "0" or str(group_id) == "None":
        group_id = None
    
    item_count = int(request.form.get('item_count', 0))
    date = request.form.get('expense_date', datetime.today().strftime('%Y-%m-%d'))
    saved_count = 0
    
    for i in range(item_count):
        item_name = request.form.get(f"name_{i}")
        amount = float(request.form.get(f"amount_{i}", 0))
        
        if item_name and amount > 0:
            add_expense(group_id, user_id, date, item_name, amount, user_id, "even")
            saved_count += 1

    # clears the temporary data from the session
    session.pop('staged_receipt_items', None)
    session.pop('staged_expense_group', None)
    
    if saved_count > 0:
        flash(f"Successfully saved {saved_count} items to the ledger!", "success")
    else:
        flash("No items were saved.", "warning")
        
    return redirect(url_for('activity.index', group_id=group_id or 0))