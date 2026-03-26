from flask import Blueprint, request, session, redirect, url_for, flash, jsonify
from src.app.database import add_subscription, delete_subscription, update_subscription

subscriptions = Blueprint('subscriptions', __name__)

@subscriptions.route('/subscriptions/add', methods=['POST'])
def add():
    if "user_id" not in session:
        return redirect(url_for('auth.login'))
        
    group_id = request.form.get('group_id')
    if not group_id or group_id == "0" or group_id == "None":
        group_id = None
    else:
        group_id = int(group_id)
        
    name = request.form.get('expense_name')
    amount = float(request.form.get('amount', 0))
    day = request.form.get('billing_day', type=int)
    
    if name and amount > 0:
        add_subscription(session['user_id'], group_id, name, amount, day)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "success"})
        flash(f"Added subscription expense: {name}", "success")
        
    return redirect(url_for('activity.index', group_id=group_id or 0))

@subscriptions.route('/subscription/edit/<int:subscription_id>', methods=['POST'])
def edit(subscription_id):
    group_id = request.form.get('group_id')
    if not group_id or group_id == "0" or group_id == "None":
        group_id = None
    else:
        group_id = int(group_id)
        
    name = request.form.get('expense_name')
    amount = float(request.form.get('amount'))
    day = request.form.get('billing_day', type=int)
    update_subscription(subscription_id, name, amount, day)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success"})
    
    flash("Subscription updated.", "success")
    return redirect(url_for('activity.index', group_id=group_id or 0))

@subscriptions.route('/subscriptions/delete/<int:subscription_id>', methods=['POST'])
def delete(subscription_id):
    group_id = request.form.get('group_id')
    if not group_id or group_id == "0" or group_id == "None":
        group_id = None
    else:
        group_id = int(group_id)
        
    delete_subscription(subscription_id)
    flash("Subscription removed.", "info")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success"})
    
    return redirect(url_for('activity.index', group_id=group_id or 0))