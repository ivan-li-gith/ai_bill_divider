def save_tracker(user_id, df, month):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            DELETE FROM payment_tracker 
            WHERE `Billing Month` = :month AND user_id = :uid
        """), {"month": month, "uid": user_id})
    
    df_to_save = df.copy()
    df_to_save["Billing Month"] = month
    df_to_save["user_id"] = user_id
    
    cols = ["user_id", "Billing Month", "Roommate Name", "Current Month Split", "Rollover Amount", "Total Owed", "Paid"]
    df_to_save[cols].to_sql("payment_tracker", engine, if_exists="append", index=False)
    
def get_paid_status(user_id, month):
    engine = get_engine()
    query = text("""
        SELECT `Roommate Name`, `Paid` 
        FROM payment_tracker 
        WHERE `Billing Month` = :month AND user_id = :uid
    """)
    
    try:
        df = pd.read_sql(query, engine, params={"month": month, "uid": user_id})
        if not df.empty:
            return df.set_index("Roommate Name")["Paid"].to_dict()
        return {}
    except Exception:
        return {}
    

