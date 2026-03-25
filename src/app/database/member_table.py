from sqlalchemy import text
from .database import get_engine

def add_group_member(group_id, name, email, phone=""):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO group_members (group_id, member_name, member_email, member_phone)
            VALUES (:gid, :name, :email, :phone)
        """), {"gid": group_id, "name": name, "email": email, "phone": phone})
        
def delete_member(member_id):
    """Deletes a specific member from a group."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM group_members WHERE group_member_id = :mid AND role != 'owner'"), 
                     {"mid": member_id})
        
def update_member(member_id, name, email, phone=""):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE group_members 
            SET member_name = :name, member_email = :email, member_phone = :phone 
            WHERE group_member_id = :mid AND role != 'owner'
        """), {"name": name, "email": email, "phone": phone, "mid": member_id})
        
def get_group_members(group_id):
    """Fetches all members in a group directly from the members table."""
    engine = get_engine()
    # ADDED 'group_member_id' to the SELECT statement
    query = text("""
        SELECT group_member_id, member_name, member_email, member_phone, user_id, role
        FROM group_members
        WHERE group_id = :gid
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"gid": group_id}).fetchall()
        return [dict(row._asdict()) for row in result]

def get_group_member_names(group_id):
    """Returns a simple list of names for members in a group."""
    engine = get_engine()
    query = text("SELECT member_name FROM group_members WHERE group_id = :gid")
    with engine.connect() as conn:
        result = conn.execute(query, {"gid": group_id}).fetchall()
        return [row[0] for row in result]
    
def update_and_sync_member(member_id, owner_id, new_name, new_email, new_phone=""):
    """Updates a member AND syncs their info across all other groups owned by the user."""
    engine = get_engine()
    with engine.begin() as conn:
        # 1. Get the old name of this member before we change it
        result = conn.execute(text("SELECT member_name FROM group_members WHERE group_member_id = :mid"), {"mid": member_id}).fetchone()
        if not result:
            return
        old_name = result[0]
        
        # 2. Update ALL members with this old name across the user's entire account
        conn.execute(text("""
            UPDATE group_members gm
            JOIN group_list gl ON gm.group_id = gl.group_id
            SET gm.member_name = :new_name, gm.member_email = :new_email, gm.member_phone = :new_phone
            WHERE gl.owner_id = :uid AND gm.member_name = :old_name AND gm.role != 'owner'
        """), {"new_name": new_name, "new_email": new_email, "new_phone": new_phone, "uid": owner_id, "old_name": old_name})
        
        # 3. If they have an "Individual" card, update the card's title too!
        conn.execute(text("""
            UPDATE group_list
            SET group_name = :new_name
            WHERE owner_id = :uid AND group_name = :old_name AND group_type = 'individual'
        """), {"new_name": new_name, "uid": owner_id, "old_name": old_name})