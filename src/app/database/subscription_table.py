from src.app.database.db import db_session
from src.app.database.models import Subscription

def add_subscription(user_id, group_id, name, amount, day):
    new_sub = Subscription(user_id=user_id, group_id=group_id, expense_name=name, amount=amount, billing_day=day)
    db_session.add(new_sub)
    db_session.commit()

def get_subscriptions(user_id, group_id=None):
    query = db_session.query(Subscription).filter_by(user_id=user_id)
    
    if group_id is not None and group_id != 0:
        if group_id == -1:
            query = query.filter_by(group_id=None)
        else:
            query = query.filter_by(group_id=group_id)
            
    subs = query.all()
    
    return [{
        "subscription_id": s.subscription_id, "group_id": s.group_id, 
        "expense_name": s.expense_name, "amount": s.amount, 
        "billing_day": s.billing_day, "group_name": s.group.group_name if s.group else "Just Me"
    } for s in subs]

def update_subscription(subscription_id, name, amount, day):
    sub = db_session.query(Subscription).filter_by(subscription_id=subscription_id).first()
    if sub:
        sub.expense_name = name
        sub.amount = amount
        sub.billing_day = day
        db_session.commit()

def delete_subscription(subscription_id):
    sub = db_session.query(Subscription).filter_by(subscription_id=subscription_id).first()
    if sub:
        db_session.delete(sub)
        db_session.commit()