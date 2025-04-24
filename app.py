import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import datetime
from datetime import date
import os
import json
from utils import (
    load_data, 
    save_data, 
    calculate_monthly_income, 
    calculate_monthly_expenses, 
    calculate_monthly_savings,
    calculate_budget_vs_actual,
    get_expense_categories,
    get_income_categories
)

# Page configuration
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# Main dashboard
st.title("Personal Finance Dashboard")

# Overview metrics
col1, col2, col3, col4 = st.columns(4)

# Get current month and year
current_month = datetime.datetime.now().month
current_year = datetime.datetime.now().year
month_name = datetime.datetime.now().strftime('%B')

# Calculate monthly totals
monthly_income = calculate_monthly_income(st.session_state.data, current_month, current_year)
monthly_expenses = calculate_monthly_expenses(st.session_state.data, current_month, current_year)
monthly_savings = calculate_monthly_savings(st.session_state.data, current_month, current_year)
budget_vs_actual = calculate_budget_vs_actual(st.session_state.data, current_month, current_year)

# Display metrics
with col1:
    st.metric(label=f"{month_name} Income", value=f"₵{monthly_income:.2f}")

with col2:
    st.metric(label=f"{month_name} Expenses", value=f"₵{monthly_expenses:.2f}")

with col3:
    st.metric(label=f"{month_name} Savings", value=f"₵{monthly_savings:.2f}")

with col4:
    if budget_vs_actual < 0:
        st.metric(label="Budget Status", value=f"₵{abs(budget_vs_actual):.2f} Over Budget", delta=budget_vs_actual, delta_color="inverse")
    else:
        st.metric(label="Budget Status", value=f"₵{budget_vs_actual:.2f} Under Budget", delta=budget_vs_actual, delta_color="normal")

# Income vs Expenses chart - Last 6 months
st.subheader("Income vs Expenses - Last 6 Months")

# Calculate data for last 6 months
months = []
incomes = []
expenses = []

for i in range(5, -1, -1):
    month_date = datetime.datetime.now() - datetime.timedelta(days=30*i)
    month_num = month_date.month
    year_num = month_date.year
    month_label = month_date.strftime("%b %Y")
    
    monthly_inc = calculate_monthly_income(st.session_state.data, month_num, year_num)
    monthly_exp = calculate_monthly_expenses(st.session_state.data, month_num, year_num)
    
    months.append(month_label)
    incomes.append(monthly_inc)
    expenses.append(monthly_exp)

# Create income vs expenses chart
fig = go.Figure()
fig.add_trace(go.Bar(
    x=months,
    y=incomes,
    name='Income',
    marker_color='#1E88E5'
))
fig.add_trace(go.Bar(
    x=months,
    y=expenses,
    name='Expenses',
    marker_color='#FF5252'
))
fig.update_layout(
    title='',
    xaxis_title='Month',
    yaxis_title='Amount (₵)',
    barmode='group',
    height=400,
)

st.plotly_chart(fig, use_container_width=True)

# Create two columns for next charts
col1, col2 = st.columns(2)

# Expense breakdown by category
with col1:
    st.subheader(f"Expense Breakdown - {month_name}")
    
    # Get expense data by category for current month
    expense_data = {}
    for entry in st.session_state.data.get('expenses', []):
        entry_date = datetime.datetime.strptime(entry['date'], '%Y-%m-%d')
        if entry_date.month == current_month and entry_date.year == current_year:
            category = entry['category']
            amount = entry['amount']
            if category in expense_data:
                expense_data[category] += amount
            else:
                expense_data[category] = amount
    
    if expense_data:
        categories = list(expense_data.keys())
        amounts = list(expense_data.values())
        
        fig = px.pie(
            values=amounts, 
            names=categories,
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expense data for this month yet")

# Budget vs Actual by category
with col2:
    st.subheader(f"Budget vs Actual - {month_name}")
    
    # Calculate budget vs actual by category
    budget_data = {}
    actual_data = {}
    
    # Get budget data
    for entry in st.session_state.data.get('budget', []):
        if entry['month'] == current_month and entry['year'] == current_year:
            category = entry['category']
            amount = entry['amount']
            budget_data[category] = amount
    
    # Get actual expense data
    for entry in st.session_state.data.get('expenses', []):
        entry_date = datetime.datetime.strptime(entry['date'], '%Y-%m-%d')
        if entry_date.month == current_month and entry_date.year == current_year:
            category = entry['category']
            amount = entry['amount']
            if category in actual_data:
                actual_data[category] += amount
            else:
                actual_data[category] = amount
    
    # Prepare data for chart
    categories = list(set(list(budget_data.keys()) + list(actual_data.keys())))
    budget_amounts = [budget_data.get(cat, 0) for cat in categories]
    actual_amounts = [actual_data.get(cat, 0) for cat in categories]
    
    if categories:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=categories,
            y=budget_amounts,
            name='Budget',
            marker_color='#9CCC65'
        ))
        fig.add_trace(go.Bar(
            x=categories,
            y=actual_amounts,
            name='Actual',
            marker_color='#FF7043'
        ))
        fig.update_layout(
            title='',
            xaxis_title='Category',
            yaxis_title='Amount (₵)',
            barmode='group',
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No budget or expense data for this month yet")

st.markdown("---")

# Savings goal tracker
st.subheader("Savings Goal Tracker")

# Get savings goal if it exists
savings_goal = 0
for entry in st.session_state.data.get('savings_goals', []):
    if entry['active']:
        savings_goal = entry['target_amount']
        break

# Get current savings
current_savings = sum(entry['amount'] for entry in st.session_state.data.get('savings', []))

# Create savings goal progress chart
if savings_goal > 0:
    progress = min(1.0, current_savings / savings_goal)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_savings,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Progress to Savings Goal"},
        delta={'reference': savings_goal, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [0, savings_goal], 'tickwidth': 1},
            'bar': {'color': "#1E88E5"},
            'threshold': {
                'line': {'color': "green", 'width': 4},
                'thickness': 0.75,
                'value': savings_goal
            }
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate time to goal based on average monthly savings
    if monthly_savings > 0:
        months_to_goal = max(0, (savings_goal - current_savings) / monthly_savings)
        if months_to_goal > 0:
            goal_date = datetime.datetime.now() + datetime.timedelta(days=30*months_to_goal)
            st.info(f"At your current savings rate, you'll reach your goal in {months_to_goal:.1f} months (around {goal_date.strftime('%B %Y')}).")
        else:
            st.success("Congratulations! You've reached your savings goal!")
    else:
        st.warning("Based on your current monthly savings, you need to save more to reach your goal.")
else:
    st.info("Set a savings goal in the Savings section to track your progress.")

st.markdown("---")

st.info("Navigate to different sections using the sidebar to manage your finances in detail.")
