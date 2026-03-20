from flask import Blueprint, render_template, session, redirect, url_for, request
from src.app.core.database import *
from src.app.routes.history import calculate_monthly_data
import plotly.express as px
import plotly.io as pio
import pandas as pd

home = Blueprint('home', __name__)

@home.route('/home')
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user_id = session["user_id"]
    user_groups = get_user_groups(user_id)
    group_id = request.args.get('group_id', type=int) or session.get('active_group_id')
    
    if not group_id and user_groups:
        group_id = user_groups[0]['group_id']
        
    billing_history = load_history(user_id)
    
    stats = {
        "total_owed_to_you": 0.0,
        "monthly_expense": 0.0,
        "your_share": 0.0,
        "current_month": "No Data"
    }
    
    donut_html = ""
    line_html = ""  
    
    if not billing_history.empty and group_id:
        names = get_group_members(group_id)
        month_displays = calculate_monthly_data(user_id, billing_history, names, group_id)
        
        if month_displays:
            current_month = month_displays[-1]
            stats = summary_cards(current_month, stats)
            donut_html = donut_chart(current_month)
            line_html = line_chart(billing_history, month_displays)
            
    return render_template('home.html', stats=stats, donut_html=donut_html, line_html=line_html, groups=user_groups, selected_group=group_id)      
    
def summary_cards(current_month, stats):
    stats.update({
        "current_month": current_month["month"], 
        "monthly_expense": current_month["monthly_total"], 
        "your_share": current_month["monthly_split"]
    })
    
    roommate_df = current_month["roommates"]
    stats["total_owed_to_you"] = roommate_df[(roommate_df["Roommate Name"] != "Me") & (roommate_df["Paid"] == False)]["Total Owed"].sum()
    return stats
    
def donut_chart(current_month):
    donut_fig = px.pie(
        current_month["df"], 
        values='Total Amount Due', 
        names='Service Name', 
        hole=0.4, 
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    donut_fig.update_traces(
        textinfo='label+percent', 
        textposition='inside',
        domain={'x': [0.1, 0.9], 'y': [0.1, 0.9]}   # decreases donut size
    )
    
    donut_fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=False
    )
    
    return pio.to_html(donut_fig, full_html=False, include_plotlyjs='cdn')
    
def line_chart(billing_history, month_displays):
    trend_data = [{"Month": month["month"], "Total Amount": month["monthly_total"], "Service": "All Services"} for month in month_displays]
    services = billing_history["Service Name"].unique()
    
    for service in services:
        for m in month_displays:
            # filter for specific service
            service_amount = m["df"][m["df"]["Service Name"] == service]["Total Amount Due"].sum()
            trend_data.append({"Month": m["month"], "Total Amount": service_amount, "Service": service})

    trend_df = pd.DataFrame(trend_data)
    line_fig = px.line(trend_df, x="Month", y="Total Amount", color="Service", markers=True)
    line_fig.for_each_trace(lambda t: t.update(visible=True if t.name == "All Services" else "legendonly"))
    
    # dropdown menu
    dropdown_buttons = [
        dict(
            label="All Services", 
            method="update", 
            args=[{"visible": [True if s == "All Services" else False for s in trend_df["Service"].unique()]}, 
                  {"title": "Total Spending Trend"}]
        )
    ]
    
    for service in services:
        dropdown_buttons.append(
            dict(
                label=service, 
                method="update", 
                args=[{"visible": [True if s == service else False for s in trend_df["Service"].unique()]}, 
                      {"title": f"{service} Spending Trend"}]
            )
        )

    line_fig.update_layout(
        updatemenus=[
            dict(
                active=0, 
                buttons=dropdown_buttons, 
                x=0.5, y=1.15, 
                xanchor="center", yanchor="top"
            )
        ],
        margin=dict(t=50, b=20, l=20, r=20),
        showlegend=False
    )
    
    return pio.to_html(line_fig, full_html=False, include_plotlyjs='cdn')
   