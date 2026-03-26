from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from src.app.core.parser import extract_from_receipt_image
from src.app.database import get_user_groups
from src.app.database import get_expenses, add_expense, delete_expense
from datetime import datetime

expenses = Blueprint('expenses', __name__)

@expenses.route('/expenses/upload_receipt', methods=['POST'])
def upload_receipt():
    """Handles AI vision processing for physical receipts."""
    group_id = request.form.get("group_id")
    file = request.files.get('receipt_image')
    
    if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.heic')):
        try:
            # 1. Send the image to GPT-4o Vision
            items_list = extract_from_receipt_image(file)
            
            # 2. Stage the extracted items in the session to review
            session['staged_receipt_items'] = items_list
            session['staged_expense_group'] = group_id
            flash("Receipt parsed successfully! Please review the items below.", "success")
        except Exception as e:
            flash(f"Failed to process receipt: {e}", "danger")
            
    return redirect(url_for('activity.index'))

@expenses.route('/expenses/manual_add', methods=['POST'])
def manual_add():
    """Handles manual entry and instantly saves it to DB."""
    if "user_id" not in session: return redirect(url_for('auth.login_page'))
    
    user_id = session["user_id"]
    group_id = request.form.get("group_id")
    
    if not group_id:
        group_id = None
        
    item_name = request.form.get("item_name")
    amount = float(request.form.get("amount", 0))
    date = request.form.get("date") # Assuming we add a date picker
    payer_id = user_id # Assuming owner is the payer for simplicity
    split_method = "even" # Default

    if item_name and amount > 0:
        try:
            # INSTANT SAVE (Instead of staging)
            add_expense(group_id, user_id, date, item_name, amount, payer_id, split_method)
            flash(f"'{item_name}' added to ledger.", "success")
        except Exception as e:
            flash(f"Error saving expense: {e}", "danger")
            
    # Redirect back to the index for that specific group
    return redirect(url_for('activity.index', group_id=group_id))

@expenses.route('/expenses/delete/<int:expense_id>', methods=['POST'])
def delete(expense_id):
    """Deletes an expense and returns the user to the ledger."""
    if "user_id" not in session:
        return redirect(url_for('auth.login_page'))
        
    try:
        delete_expense(expense_id)
        flash("Expense deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting expense: {e}", "danger")
        
    return redirect(url_for('activity.index'))

@expenses.route('/expenses/save_staged', methods=['POST'])
def save_staged():
    """Takes the reviewed receipt items from the UI and saves them to the DB."""
    if "user_id" not in session: 
        return redirect(url_for('auth.login_page'))
    
    user_id = session['user_id']
    group_id = session.get('staged_expense_group')
    
    if not group_id:
        group_id = None
    
    item_count = int(request.form.get('item_count', 0))
    date = request.form.get('expense_date', datetime.today().strftime('%Y-%m-%d'))

    saved_count = 0
    for i in range(item_count):
        item_name = request.form.get(f"name_{i}")
        amount = float(request.form.get(f"amount_{i}", 0))
        
        # Save each item as a separate expense, assuming an even split for now
        if item_name and amount > 0:
            add_expense(group_id, user_id, date, item_name, amount, user_id, "even")
            saved_count += 1

    # Clear the temporary data from the session
    session.pop('staged_receipt_items', None)
    session.pop('staged_expense_group', None)
    
    if saved_count > 0:
        flash(f"Successfully saved {saved_count} items to the ledger!", "success")
    else:
        flash("No items were saved.", "warning")
        
    return redirect(url_for('activity.index', group_id=group_id))