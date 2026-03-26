from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from src.app.database import (
    get_user_groups, 
    get_subscriptions, 
    add_subscription, 
    delete_subscription,
    update_subscription
)

subscriptions = Blueprint('subscriptions', __name__)

@subscriptions.route('/subscriptions/add', methods=['POST'])
def add():
    if "user_id" not in session:
        return redirect(url_for('auth.login_page'))
        
    group_id = request.form.get('group_id', type=int)
    name = request.form.get('expense_name')
    amount = float(request.form.get('amount', 0))
    day = request.form.get('billing_day', type=int)
    
    if name and amount > 0:
        add_subscription(session['user_id'], group_id, name, amount, day)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "success"})
        flash(f"Added subscription expense: {name}", "success")
        
    return redirect(url_for('activity.index', group_id=group_id))

@subscriptions.route('/subscription/edit/<int:subscription_id>', methods=['POST'])
def edit(subscription_id):
    group_id = request.form.get('group_id')
    name = request.form.get('expense_name')
    amount = float(request.form.get('amount'))
    day = request.form.get('billing_day', type=int)
    
    update_subscription(subscription_id, name, amount, day)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success"})
    flash("Subscription updated.", "success")
    return redirect(url_for('activity.index', group_id=group_id))

@subscriptions.route('/subscriptions/delete/<int:subscription_id>', methods=['POST'])
def delete(subscription_id):
    group_id = request.form.get('group_id')
    delete_subscription(subscription_id)
    flash("Subscription removed.", "info")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success"})
    
    return redirect(url_for('activity.index', group_id=group_id))