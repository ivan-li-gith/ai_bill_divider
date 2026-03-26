from src.app.database.db import db_session
from src.app.database.models import Expense, ExpenseSplit, GroupMember

# creates a new expense and splits it based on the group members
def add_expense(group_id, user_id, date, item_name, amount, payer_id, split_method):
    new_expense = Expense(
        group_id=group_id, user_id=user_id, expense_date=date, 
        description=item_name, amount=amount, payer_id=payer_id, split_method=split_method
    )
    db_session.add(new_expense)
    db_session.flush() 
    
    if group_id is None:
        db_session.commit()
        return
    
    members = db_session.query(GroupMember).filter_by(group_id=group_id).all()
    if not members:
        db_session.rollback()
        return
        
    num_people = len(members)
    split_amount = round(amount / num_people, 2)
    
    for member in members:
        is_payer = str(member.user_id) == str(payer_id)
        if not is_payer:
            new_split = ExpenseSplit(
                expense_id=new_expense.expense_id, 
                roommate_name=member.member_name, 
                amount_owed=split_amount, 
                is_paid=False
            )
            db_session.add(new_split)
            
    db_session.commit()

# fetches expenses for a group
def get_expenses(group_id, user_id=None):
    query = db_session.query(Expense)
    
    if group_id is not None and group_id != -1:
        query = query.filter_by(group_id=group_id)
    else:
        if user_id:
            query = query.filter_by(group_id=None, user_id=user_id)
        else:
            query = query.filter_by(group_id=None)
            
    expenses = query.order_by(Expense.expense_date.desc()).all()
    return [{
        "expense_id": e.expense_id, "expense_date": e.expense_date, 
        "description": e.description, "amount": e.amount, 
        "payer_id": e.payer_id, "split_method": e.split_method,
        "group_name": e.group.group_name if e.group else "Just Me"
    } for e in expenses]
 
def delete_expense(expense_id):
    expense = db_session.query(Expense).filter_by(expense_id=expense_id).first()
    if expense:
        db_session.delete(expense) 
        db_session.commit()
 
# calculates total debt owed by each roommate    
def get_unpaid_expense_splits(group_id=None):
    query = db_session.query(ExpenseSplit).join(Expense).filter(ExpenseSplit.is_paid == False)
    
    if group_id and group_id != 0:
        query = query.filter(Expense.group_id == group_id)
        
    splits = query.all()
    
    totals = {}
    for split in splits:
        totals[split.roommate_name] = totals.get(split.roommate_name, 0.0) + float(split.amount_owed)
        
    return totals