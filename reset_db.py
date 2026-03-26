# reset_db.py
from src.app.database import engine
from sqlalchemy import text

with engine.begin() as conn:
    print("WARNING: Deleting ALL application data...")
    
    # 1. Disable foreign key checks to allow "force" delete
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    
    # Updated table names based on the refactored models.py
    tables = [
        "profiles",
        "groups",
        "group_members",
        "utility_bills",
        "utility_splits",
        "subscriptions",
        "expenses",
        "expense_splits"
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