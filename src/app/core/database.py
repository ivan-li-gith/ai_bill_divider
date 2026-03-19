import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS") 
DB_NAME = os.environ.get("DB_NAME")

def get_engine():
    connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"
    return create_engine(connection_string)

def init_db():
    engine = get_engine()
    with engine.begin() as conn:
        # user profile table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS profiles (
                user_id VARCHAR(255) PRIMARY KEY,
                display_name VARCHAR(255),
                age INT,
                email VARCHAR(255)
            )  
        """))
        
        # group category table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS group_list (
                group_id INT AUTO_INCREMENT PRIMARY KEY,
                group_name VARCHAR(255),
                owner_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS group_members (
                group_member_id INT AUTO_INCREMENT PRIMARY KEY,
                group_id INT,
                member_name VARCHAR(255),
                member_email VARCHAR(255),
                user_id VARCHAR(255) NULL,
                role VARCHAR(50) DEFAULT 'member',
                FOREIGN KEY (group_id) REFERENCES group_list(group_id)
            )
        """))
        
        # bill_history table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bill_history (
                bill_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                group_id INT,
                `Billing Month` VARCHAR(255),
                `Service Name` VARCHAR(255),
                `Service Period` VARCHAR(255),
                `Total Amount Due` DECIMAL(10, 2)
            )
        """))
        
        # payment_tracker table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payment_tracker (
                user_id VARCHAR(255),
                group_id INT,
                `Billing Month` VARCHAR(255),
                `Roommate Name` VARCHAR(255),
                `Current Month Split` DECIMAL(10, 2),
                `Rollover Amount` DECIMAL(10, 2),
                `Total Owed` DECIMAL(10, 2),
                `Paid` BOOLEAN
            )
        """))
        
        # roommates table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS roommates (
                user_id VARCHAR(255),
                `Roommate Name` VARCHAR(255),
                UNIQUE(user_id, `Roommate Name`)
            )
        """))

def load_history(user_id):
    engine = get_engine()
    query = text("SELECT * FROM bill_history WHERE user_id = :uid")
    return pd.read_sql(query, engine, params={"uid": user_id})

def clear_db(user_id):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM bill_history WHERE user_id = :uid"), {"uid": user_id})
        conn.execute(text("DELETE FROM payment_tracker WHERE user_id = :uid"), {"uid": user_id})

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

def get_roommates(user_id):
    engine = get_engine()
    query = text("SELECT `Roommate Name` FROM roommates WHERE user_id = :uid")
    
    try:
        df = pd.read_sql(query, engine, params={"uid": user_id})
        return df["Roommate Name"].tolist()
    except Exception:
        return []

def add_roommate(user_id, name):
    engine = get_engine()
    name = name.strip()
    if not name:
        return
    with engine.begin() as conn:
        try:
            conn.execute(text("""
                INSERT INTO roommates (user_id, `Roommate Name`)
                VALUES (:uid, :name)
            """), {"uid": user_id, "name": name})
        except Exception: 
            pass

def remove_roommate(user_id, name):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            DELETE FROM roommates 
            WHERE user_id = :uid AND `Roommate Name` = :name
        """), {"uid": user_id, "name": name})

def save_bill_history(user_id, df):
    engine = get_engine()
    df_to_save = df.copy()
    df_to_save["user_id"] = user_id
    df_to_save.to_sql("bill_history", engine, if_exists="append", index=False)

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
    
def get_profile(user_id):
    engine = get_engine()
    query = text("SELECT * FROM profiles WHERE user_id = :uid")
    
    with engine.connect() as conn:
        result = conn.execute(query, {"uid": user_id}).fetchone()
        return result._asdict() if result else None
    
def save_profile(user_id, name, age):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO profiles (user_id, display_name, age)
            VALUES (:uid, :name, :age)
            ON DUPLICATE KEY UPDATE display_name = :name, age = :age
        """), {"uid": user_id, "name": name, "age": age})
        
def create_group(owner_id, group_name):
    engine = get_engine()
    with engine.begin() as conn:
        # Create the group record
        result = conn.execute(text("""
            INSERT INTO group_list (group_name, owner_id)
            VALUES (:name, :oid)
        """), {"name": group_name, "oid": owner_id})
        
        group_id = result.lastrowid
        
        # Fetch owner's profile info to add them as the first member
        profile = conn.execute(text("SELECT display_name, email FROM profiles WHERE user_id = :uid"), 
                               {"uid": owner_id}).fetchone()
        
        name = profile.display_name if profile else "Owner"
        email = profile.email if profile else ""

        # Add owner as a member
        conn.execute(text("""
            INSERT INTO group_members (group_id, member_name, member_email, user_id, role)
            VALUES (:gid, :name, :email, :uid, 'owner')
        """), {"gid": group_id, "name": name, "email": email, "uid": owner_id})
        
        return group_id
    
# src/app/core/database.py

def get_user_groups(user_id):
    """Fetches groups and includes a JSON string of member details."""
    engine = get_engine()
    # Use JSON_ARRAYAGG and JSON_OBJECT for structured member data
    query = text("""
        SELECT gl.group_id, gl.group_name, gl.owner_id,
               JSON_ARRAYAGG(
                   JSON_OBJECT(
                       'id', gm.group_member_id,
                       'name', gm.member_name,
                       'email', gm.member_email,
                       'role', gm.role
                   )
               ) as members_json
        FROM group_list gl
        JOIN group_members gm ON gl.group_id = gm.group_id
        WHERE gl.owner_id = :uid OR gm.user_id = :uid
        GROUP BY gl.group_id
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"uid": user_id}).fetchall()
        return [dict(row._asdict()) for row in result]

def delete_group(group_id, user_id):
    """Deletes group if the user is the owner."""
    engine = get_engine()
    with engine.begin() as conn:
        # First remove members (FK constraint)
        conn.execute(text("DELETE FROM group_members WHERE group_id = :gid"), {"gid": group_id})
        # Then remove the group
        conn.execute(text("DELETE FROM group_list WHERE group_id = :gid AND owner_id = :uid"), 
                     {"gid": group_id, "uid": user_id})

def update_group_name(group_id, new_name):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("UPDATE group_list SET group_name = :name WHERE group_id = :gid"), 
                     {"name": new_name, "gid": group_id})

def get_group_members(group_id):
    """Fetches all profiles of users in a specific group."""
    engine = get_engine()
    query = text("""
        SELECT p.user_id, p.display_name, p.email, gm.role
        FROM profiles p
        JOIN group_members gm ON p.user_id = gm.user_id
        WHERE gm.group_id = :gid
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"gid": group_id}).fetchall()
        return [dict(row._asdict()) for row in result]

def get_user_by_email(email):
    """Finds a user's ID by their email."""
    engine = get_engine()
    query = text("SELECT user_id FROM profiles WHERE email = :email")
    with engine.connect() as conn:
        result = conn.execute(query, {"email": email}).fetchone()
        return result[0] if result else None

def add_group_member(group_id, name, email):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO group_members (group_id, member_name, member_email)
            VALUES (:gid, :name, :email)
        """), {"gid": group_id, "name": name, "email": email})
        
def delete_member(member_id):
    """Deletes a specific member from a group."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM group_members WHERE group_member_id = :mid AND role != 'owner'"), 
                     {"mid": member_id})