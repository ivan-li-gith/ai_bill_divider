from src.app.database.db import db_session
from src.app.database.models import Group, GroupMember, Profile

def create_group(owner_id, group_name, group_type='group'):
    new_group = Group(group_name=group_name, owner_id=owner_id, group_type=group_type)
    db_session.add(new_group)
    db_session.flush()
    profile = db_session.query(Profile).filter_by(user_id=owner_id).first()
    name = profile.display_name if profile else "Owner"
    email = profile.email if profile else ""

    owner_member = GroupMember(
        group_id=new_group.group_id, 
        member_name=name, 
        member_email=email, 
        user_id=owner_id, 
        role='owner'
    )
    db_session.add(owner_member)
    db_session.commit()
    
    return new_group.group_id

def get_user_groups(user_id):
    groups = db_session.query(Group).join(Group.members).filter(
        (Group.owner_id == user_id) | (GroupMember.user_id == user_id)
    ).distinct().all()
    
    result = []
    for g in groups:
        members_list = [{
            'id': m.group_member_id,
            'name': m.member_name,
            'email': m.member_email,
            'role': m.role
        } for m in g.members]
        
        result.append({
            "group_id": g.group_id,
            "group_name": g.group_name,
            "owner_id": g.owner_id,
            "group_type": g.group_type,
            "members_json": members_list 
        })
    return result

def delete_group(group_id, user_id):
    group = db_session.query(Group).filter_by(group_id=group_id, owner_id=user_id).first()
    if group:
        db_session.delete(group)
        db_session.commit()

def update_group_name(group_id, new_name):
    group = db_session.query(Group).filter_by(group_id=group_id).first()
    if group:
        group.group_name = new_name
        db_session.commit()