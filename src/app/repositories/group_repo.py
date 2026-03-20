        
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