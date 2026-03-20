# reset_db.py
from src.app.database import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.begin() as conn:
    print("WARNING: Deleting ALL application data...")
    
    # 1. Disable foreign key checks to allow "force" delete
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    
    tables = [
        "payment_tracker", 
        "bill_history", 
        "group_members", 
        "group_list", 
        "roommates", 
        "profiles",
        "recurring_expenses"
    ]
    
    for table in tables:
        try:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            print(f"Dropped {table}")
        except Exception as e:
            print(f"Failed to drop {table}: {e}")
    
    # 2. Re-enable foreign key checks
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    
    print("\nDatabase is now empty. Restart the app to recreate the new schema.")