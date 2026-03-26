from src.app.database.db import db_session
from src.app.database.models import GroupMember, Group

def add_group_member(group_id, name, email):
    new_member = GroupMember(group_id=group_id, member_name=name, member_email=email)
    db_session.add(new_member)
    db_session.commit()
        
def delete_member(member_id):
    member = db_session.query(GroupMember).filter_by(group_member_id=member_id).filter(GroupMember.role != 'owner').first()
    if member:
        db_session.delete(member)
        db_session.commit()
        
def update_member(member_id, name, email):
    member = db_session.query(GroupMember).filter_by(group_member_id=member_id).filter(GroupMember.role != 'owner').first()
    if member:
        member.member_name = name
        member.member_email = email
        db_session.commit()
        
def get_group_members(group_id):
    members = db_session.query(GroupMember).filter_by(group_id=group_id).all()
    return [{
        "group_member_id": m.group_member_id, "member_name": m.member_name, 
        "member_email": m.member_email, 
        "user_id": m.user_id, "role": m.role
    } for m in members]

def get_group_member_names(group_id):
    members = db_session.query(GroupMember.member_name).filter_by(group_id=group_id).all()
    return [m.member_name for m in members]
    
def update_and_sync_member(member_id, owner_id, new_name, new_email):
    target_member = db_session.query(GroupMember).filter_by(group_member_id=member_id).first()
    if not target_member:
        return
        
    old_name = target_member.member_name
    
    members_to_update = db_session.query(GroupMember).join(Group).filter(
        Group.owner_id == owner_id, 
        GroupMember.member_name == old_name, 
        GroupMember.role != 'owner'
    ).all()
    
    for m in members_to_update:
        m.member_name = new_name
        m.member_email = new_email
        
    individual_group = db_session.query(Group).filter_by(owner_id=owner_id, group_name=old_name, group_type='individual').first()
    if individual_group:
        individual_group.group_name = new_name
        
    db_session.commit()