from flask import Blueprint, render_template, request, session, redirect, url_for
from src.app.database import get_user_groups, get_utility_bills, get_subscriptions, get_expenses, get_group_members
from src.app.services.utility_service import calculate_utilities, get_member_names

activity = Blueprint('activity', __name__)

@activity.route('/activity')
def index():
    if "user_id" not in session:
        return redirect(url_for('auth.login_page'))
    
    user_id = session["user_id"]
    user_groups = get_user_groups(user_id)
    
    # Default to 0 (ALL) if no filter is applied
    group_id = request.args.get('group_id', type=int)
    if group_id is None:
        group_id = 0

    exps = []
    subs = []
    month_displays = []

    if group_id == 0:
        # Fetch all subscriptions
        subs = get_subscriptions(user_id, 0)
        
        # Iterate through every group to fetch and combine expenses & utilities
        for g in user_groups:
            gid = g['group_id']
            
            g_exps = get_expenses(gid)
            exps.extend(g_exps)
            
            b_history = get_utility_bills(user_id, gid)
            if not b_history.empty:
                members = get_group_members(gid)
                names = get_member_names(user_id, members)
                md = calculate_utilities(user_id, b_history, names, gid)
                
                # Append the group name so you know which house/group the bill is for in the 'ALL' view
                for m in md:
                    m['display_title'] = f"{m['month']} ({g['group_name']})"
                month_displays.extend(md)
                
        # Sort to show newest first
        exps.sort(key=lambda x: str(x['expense_date']), reverse=True)
        month_displays.reverse()
        
    else:
        # Fetch data for only the specifically selected group
        exps = get_expenses(group_id)
        subs = get_subscriptions(user_id, group_id)

        billing_history = get_utility_bills(user_id, group_id)
        if not billing_history.empty:
            members = get_group_members(group_id)
            names = get_member_names(user_id, members)
            month_displays = calculate_utilities(user_id, billing_history, names, group_id)
            for m in month_displays:
                m['display_title'] = m['month']
            month_displays.reverse()

    return render_template('activity.html', 
                           groups=user_groups, 
                           selected_group_id=group_id,
                           expenses=exps,
                           subscriptions=subs,
                           month_displays=month_displays)