import pandas as pd
from sqlalchemy import text
from src.app.database.db import db_session, engine
from src.app.database.models import UtilitySplit

def save_utility_bills(user_id, df):
    df_mapped = df.rename(columns={
        "Billing Month": "billing_month",
        "Service Name": "service_name",
        "Service Period": "service_period",
        "Total Amount Due": "total_amount_due"
    })
    df_mapped["user_id"] = user_id
    df_mapped.to_sql("utility_bills", engine, if_exists="append", index=False)

def get_utility_bills(user_id, group_id=None):
    if group_id is not None and group_id != 0:
        if group_id == -1:
            query = text("SELECT * FROM utility_bills WHERE user_id = :uid AND group_id IS NULL")
            df = pd.read_sql(query, engine, params={"uid": user_id})
        else:
            query = text("SELECT * FROM utility_bills WHERE user_id = :uid AND group_id = :gid")
            df = pd.read_sql(query, engine, params={"uid": user_id, "gid": group_id})
    else:
        query = text("SELECT * FROM utility_bills WHERE user_id = :uid")
        df = pd.read_sql(query, engine, params={"uid": user_id})
        
    if not df.empty:
        df = df.rename(columns={
            "billing_month": "Billing Month",
            "service_name": "Service Name",
            "service_period": "Service Period",
            "total_amount_due": "Total Amount Due"
        })
    return df

# deletes old records and saves new record 
def save_utility_splits(user_id, df, month, group_id):
    db_group_id = None if group_id == -1 else group_id
    
    if db_group_id is None:
        db_session.query(UtilitySplit).filter_by(billing_month=month, user_id=user_id, group_id=None).delete()
    else:
        db_session.query(UtilitySplit).filter_by(billing_month=month, user_id=user_id, group_id=db_group_id).delete()
    db_session.commit()
    
    df_mapped = df.rename(columns={
        "Roommate Name": "roommate_name",
        "Current Month Split": "current_month_split",
        "Rollover Amount": "rollover_amount",
        "Total Owed": "total_owed",
        "Paid": "is_paid"
    })
    df_mapped["billing_month"] = month
    df_mapped["user_id"] = user_id
    df_mapped["group_id"] = db_group_id
    
    cols = ["user_id", "group_id", "billing_month", "roommate_name", "current_month_split", "rollover_amount", "total_owed", "is_paid"]
    df_mapped[cols].to_sql("utility_splits", engine, if_exists="append", index=False)

# tells us who has paid
def get_utility_split_status(user_id, month, group_id):
    if group_id is None or group_id == -1:
        splits = db_session.query(UtilitySplit).filter_by(billing_month=month, user_id=user_id, group_id=None).all()
    else:
        splits = db_session.query(UtilitySplit).filter_by(billing_month=month, user_id=user_id, group_id=group_id).all()
    return {split.roommate_name: split.is_paid for split in splits}