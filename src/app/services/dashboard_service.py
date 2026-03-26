import json
from datetime import datetime
from src.app.database import get_user_groups, get_utility_bills, get_group_members, get_unpaid_expense_splits, get_subscriptions
from src.app.services.utility_service import calculate_utilities, get_member_names
from src.app.database.models import Expense, Subscription, UtilityBill
from src.app.database.db import db_session

# updates members debt
def add_debt(name, category, amount, debtors_dict, contact_map):
    if amount <= 0: return
    if name not in debtors_dict:
        contact = contact_map.get(name, {})
        debtors_dict[name] = {
            'name': name, 'utilities': 0.0, 'expenses': 0.0, 'subscriptions': 0.0, 'total': 0.0,
            'email': contact.get('email', '')
        }
    debtors_dict[name][category] += amount
    debtors_dict[name]['total'] += amount

# grabs all utilities, expenses, and subscriptions and displays it into a dashboard
def get_dashboard_metrics(user_id, group_id):
    """Calculates all outstanding debts for the dashboard."""
    user_groups = get_user_groups(user_id)
    debtors_dict = {}
    contact_map = {}
    
    # contacts
    for group in user_groups:
        members = group.get('members_json', [])
        if isinstance(members, str): 
            members = json.loads(members)
        for member in (members or []):
            if member.get('name') not in contact_map:
                contact_map[member.get('name')] = {
                    'email': member.get('email', '')
                }

    groups_to_check = [group_id] if group_id != 0 else [g['group_id'] for g in user_groups]
    
    for gid in groups_to_check:
        # utilities
        billing_history = get_utility_bills(user_id, gid)
        if not billing_history.empty:
            members = get_group_members(gid)
            names = get_member_names(user_id, members)
            month_displays = calculate_utilities(user_id, billing_history, names, gid)
            
            if month_displays:
                latest_month = month_displays[-1]["roommates"]
                for _, row in latest_month.iterrows():
                    name = row["Roommate Name"]
                    if name != "Me" and not row["Paid"] and row["Total Owed"] > 0:
                        add_debt(name, 'utilities', row["Total Owed"], debtors_dict, contact_map)
                        
        # expenses
        unpaid_exps = get_unpaid_expense_splits(gid)
        for name, amt in unpaid_exps.items():
            if name != "Me":
                add_debt(name, 'expenses', amt, debtors_dict, contact_map)
                
        # subscriptions
        subs = get_subscriptions(user_id, gid)
        if subs:
            current_day = datetime.today().day
            members = get_group_members(gid)
            num_people = len(members)
            
            if num_people > 0:
                for sub in subs:
                    if current_day >= sub['billing_day']:
                        split_amt = round(float(sub['amount']) / num_people, 2)
                        for m in members:
                            if m.get('role') != 'owner':
                                add_debt(m['member_name'], 'subscriptions', split_amt, debtors_dict, contact_map)
        
    debtors = list(debtors_dict.values())
    total_uncollected = sum(d['total'] for d in debtors)

    # calculate personal expenses
    my_expenses_total = 0.0
    
    utils = db_session.query(UtilityBill).filter_by(user_id=user_id).filter(UtilityBill.group_id.is_(None)).all()
    my_expenses_total += sum(float(u.total_amount_due or 0) for u in utils)
    
    exps = db_session.query(Expense).filter_by(user_id=user_id).filter(Expense.group_id.is_(None)).all()
    my_expenses_total += sum(float(e.amount or 0) for e in exps)
    
    subs = db_session.query(Subscription).filter_by(user_id=user_id).filter(Subscription.group_id.is_(None)).all()
    my_expenses_total += sum(float(s.amount or 0) for s in subs)

    return debtors, total_uncollected, user_groups, my_expenses_total