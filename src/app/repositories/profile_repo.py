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
        
def get_user_by_email(email):
    """Finds a user's ID by their email."""
    engine = get_engine()
    query = text("SELECT user_id FROM profiles WHERE email = :email")
    with engine.connect() as conn:
        result = conn.execute(query, {"email": email}).fetchone()
        return result[0] if result else None