from flask import Blueprint, render_template, request, session, redirect, url_for
from src.app.database import get_user_groups, get_utility_bills, get_subscriptions, get_expenses, get_group_members
from src.app.services.utility_service import calculate_utilities, get_member_names

activity = Blueprint('activity', __name__)

@activity.route('/activity')
def index():
    if "user_id" not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session["user_id"]
    user_groups = get_user_groups(user_id)
    
    # defaults to all if no filter is selected
    group_id = request.args.get('group_id', type=int)
    if group_id is None:
        group_id = 0

    exps = []
    subs = []
    month_displays = []

    # all groups 
    if group_id == 0:
        subs = get_subscriptions(user_id, 0)
        personal_exps = get_expenses(None, user_id=user_id)
        exps.extend(personal_exps)
        
        b_history_personal = get_utility_bills(user_id, -1)
        if not b_history_personal.empty:
            md = calculate_utilities(user_id, b_history_personal, ["Me"], None)
            for m in md:
                m['display_title'] = f"{m['month']} (Just Me)"
            month_displays.extend(md)

        for g in user_groups:
            gid = g['group_id']
            g_exps = get_expenses(gid, user_id=user_id)
            exps.extend(g_exps)
            b_history = get_utility_bills(user_id, gid)
            
            if not b_history.empty:
                members = get_group_members(gid)
                names = get_member_names(user_id, members)
                md = calculate_utilities(user_id, b_history, names, gid)
                
                for m in md:
                    m['display_title'] = f"{m['month']} ({g['group_name']})"
                month_displays.extend(md)
                
        exps.sort(key=lambda x: str(x['expense_date']), reverse=True)
        month_displays.reverse()

    # just me
    elif group_id == -1:
        exps = get_expenses(None, user_id=user_id)
        subs = get_subscriptions(user_id, -1)
        b_history_personal = get_utility_bills(user_id, -1)
        if not b_history_personal.empty:
            md = calculate_utilities(user_id, b_history_personal, ["Me"], None)
            for m in md:
                m['display_title'] = f"{m['month']} (Just Me)"
            month_displays.extend(md)
        month_displays.reverse()

    # specific group
    else:
        exps = get_expenses(group_id, user_id=user_id)
        subs = get_subscriptions(user_id, group_id)
        billing_history = get_utility_bills(user_id, group_id)
        
        if not billing_history.empty:
            members = get_group_members(group_id)
            names = get_member_names(user_id, members)
            month_displays = calculate_utilities(user_id, billing_history, names, group_id)
            for m in month_displays:
                m['display_title'] = m['month']
            month_displays.reverse()

    return render_template('activity.html', groups=user_groups, selected_group_id=group_id, expenses=exps, subscriptions=subs, month_displays=month_displays)