
def save_bill_history(user_id, df):
    engine = get_engine()
    df_to_save = df.copy()
    df_to_save["user_id"] = user_id
    df_to_save.to_sql("bill_history", engine, if_exists="append", index=False)