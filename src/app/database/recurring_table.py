from sqlalchemy import text
from .database import get_engine

def add_recurring_expense(user_id, group_id, name, amount, day):
    """Adds a new fixed recurring expense rule including the billing day."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO recurring_expenses (user_id, group_id, expense_name, amount, billing_day)
            VALUES (:uid, :gid, :name, :amount, :day)
        """), {"uid": user_id, "gid": group_id, "name": name, "amount": amount, "day": day})

def get_recurring_expenses(group_id):
    """Fetches all recurring expense rules for a specific group."""
    engine = get_engine()
    query = text("""
        SELECT recurring_id, expense_name, amount, billing_day 
        FROM recurring_expenses 
        WHERE group_id = :gid
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"gid": group_id}).fetchall()
        return [dict(row._asdict()) for row in result]

def update_recurring_expense(recurring_id, name, amount, day):
    """Updates an existing recurring expense including the billing day."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE recurring_expenses 
            SET expense_name = :name, amount = :amount, billing_day = :day 
            WHERE recurring_id = :rid
        """), {"name": name, "amount": amount, "day": day, "rid": recurring_id})

def delete_recurring_expense(recurring_id):
    """Permanently removes a recurring expense rule."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM recurring_expenses WHERE recurring_id = :rid"), 
                     {"rid": recurring_id})