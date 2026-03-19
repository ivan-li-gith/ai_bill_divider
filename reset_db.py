# reset_db.py
from src.app.core.database import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.begin() as conn:
    print("WARNING: Deleting ALL application data...")
    # Drop tables in specific order to avoid foreign key issues
    tables = [
        "payment_tracker", 
        "bill_history", 
        "group_members", 
        "group_list", 
        "roommates", 
        "profiles"
    ]
    for table in tables:
        conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        print(f"Dropped {table}")
    
    print("\nDatabase is now empty. Restart the app to recreate the new schema.")