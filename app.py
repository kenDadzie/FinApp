import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import datetime
from datetime import date

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

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Load or initialize data ───────────────────────────────────────────────────
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# ─── Sidebar navigation ────────────────────────────────────────────────────────
st.sidebar.title("Personal Finance")
page = st.sidebar.radio("Go to", [
    "Dashboard",
    "Add Income",
    "Add Expense",
    "Set Budget",
    "Set Savings Goal",
])

# ─── Dashboard ────────────────────────────────────────────────────────────────
if page == "Dashboard":
    st.title("Personal Finance Dashboard")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    now = datetime.datetime.now()
    current_month, current_year = now.month, now.year
    month_name = now.strftime("%B")

    inc = calculate_monthly_income(st.session_state.data, current_month, current_year)
    exp = calculate_monthly_expenses(st.session_state.data, current_month, current_year)
    sav = calculate_monthly_savings(st.session_state.data, current_month, current_year)
    bud_vs_act = calculate_budget_vs_actual(st.session_state.data, current_month, current_year)

    with col1:
        st.metric(f"{month_name} Income", f"₵{inc:.2f}")
    with col2:
        st.metric(f"{month_name} Expenses", f"₵{exp:.2f}")
    with col3:
        st.metric(f"{month_name} Savings", f"₵{sav:.2f}")
    with col4:
        if bud_vs_act < 0:
            st.metric("Budget Status", f"₵{abs(bud_vs_act):.2f} Over", delta=bud_vs_act, delta_color="inverse")
        else:
            st.metric("Budget Status", f"₵{bud_vs_act:.2f} Under", delta=bud_vs_act, delta_color="normal")

    st.markdown("---")
    st.subheader("Income vs Expenses - Last 6 Months")

    # build last-6-months chart
    months, incomes, expenses = [], [], []
    for i in range(5, -1, -1):
        dt = now - datetime.timedelta(days=30*i)
        lbl = dt.strftime("%b %Y")
        months.append(lbl)
        incomes.append(calculate_monthly_income(st.session_state.data, dt.month, dt.year))
        expenses.append(calculate_monthly_expenses(st.session_state.data, dt.month, dt.year))

    fig = go.Figure([
        go.Bar(x=months, y=incomes, name="Income"),
        go.Bar(x=months, y=expenses, name="Expenses")
    ])
    fig.update_layout(barmode="group", height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Expense breakdown
    with col1:
        st.subheader(f"Expense Breakdown - {month_name}")
        data = st.session_state.data.get("expenses", [])
        breakdown = {}
        for e in data:
            d = datetime.datetime.fromisoformat(e["date"])
            if d.month == current_month and d.year == current_year:
                breakdown[e["category"]] = breakdown.get(e["category"], 0) + e["amount"]

        if breakdown:
            pie = px.pie(
                values=list(breakdown.values()),
                names=list(breakdown.keys()),
                hole=0.4
            )
            pie.update_layout(height=400)
            st.plotly_chart(pie, use_container_width=True)
        else:
            st.info("No expense data for this month yet")

    # Budget vs Actual by category
    with col2:
        st.subheader(f"Budget vs Actual - {month_name}")
        budgets = {b["category"]: b["amount"]
                   for b in st.session_state.data.get("budget", [])
                   if b["month"] == current_month and b["year"] == current_year}
        actuals = {}
        for e in st.session_state.data.get("expenses", []):
            d = datetime.datetime.fromisoformat(e["date"])
            if d.month == current_month and d.year == current_year:
                actuals[e["category"]] = actuals.get(e["category"], 0) + e["amount"]

        cats = sorted(set(budgets) | set(actuals))
        if cats:
            fig2 = go.Figure([
                go.Bar(x=cats, y=[budgets.get(c, 0) for c in cats], name="Budget"),
                go.Bar(x=cats, y=[actuals.get(c, 0) for c in cats], name="Actual")
            ])
            fig2.update_layout(barmode="group", height=400)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No budget or expense data for this month yet")

    st.markdown("---")
    st.subheader("Savings Goal Tracker")

    # Savings goal widget
    goals = st.session_state.data.get("savings_goals", [])
    active_goal = next((g for g in goals if g.get("active")), None)
    target = active_goal["target_amount"] if active_goal else 0
    saved = sum(s["amount"] for s in st.session_state.data.get("savings", []))

    if target:
        progress = min(saved / target, 1.0)
        gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=saved,
            delta={'reference': target},
            gauge={'axis': {'range': [0, target]}}
        ))
        gauge.update_layout(height=300)
        st.plotly_chart(gauge, use_container_width=True)

        if sav > 0:
            months_left = (target - saved) / sav
            eta = now + datetime.timedelta(days=30 * months_left)
            st.info(f"At this rate you'll hit your goal in {months_left:.1f} months (around {eta:%b %Y}).")
        else:
            st.warning("Increase your monthly savings to reach the goal.")
    else:
        st.info("Set a savings goal to start tracking.")

# ─── Add Income ────────────────────────────────────────────────────────────────
elif page == "Add Income":
    st.title("Add New Income")
    with st.form("income_form", clear_on_submit=True):
        d = st.date_input("Date", value=st.session_state.get("last_income_date", date.today()))
        amt = st.number_input("Amount (₵)", min_value=0.0, format="%.2f")
        cat = st.selectbox("Category", get_income_categories())
        ok = st.form_submit_button("Save Income")

    if ok:
        save_data("income", {"date": d.isoformat(), "amount": amt, "category": cat})
        st.success("Income recorded!")

# ─── Add Expense ──────────────────────────────────────────────────────────────
elif page == "Add Expense":
    st.title("Add New Expense")
    with st.form("expense_form", clear_on_submit=True):
        d = st.date_input("Date", value=st.session_state.get("last_expense_date", date.today()))
        amt = st.number_input("Amount (₵)", min_value=0.0, format="%.2f")
        cat = st.selectbox("Category", get_expense_categories())
        ok = st.form_submit_button("Save Expense")

    if ok:
        save_data("expenses", {"date": d.isoformat(), "amount": amt, "category": cat})
        st.success("Expense recorded!")

# ─── Set Budget ───────────────────────────────────────────────────────────────
elif page == "Set Budget":
    st.title("Set Monthly Budget")
    with st.form("budget_form", clear_on_submit=True):
        m = st.selectbox("Month", list(range(1, 13)), index=current_month - 1)
        y = st.number_input("Year", value=current_year, step=1)
        cat = st.selectbox("Category", get_expense_categories())
        amt = st.number_input("Budget Amount (₵)", min_value=0.0, format="%.2f")
        ok = st.form_submit_button("Save Budget")

    if ok:
        save_data("budget", {"month": m, "year": y, "category": cat, "amount": amt})
        st.success("Budget saved!")

# ─── Set Savings Goal ─────────────────────────────────────────────────────────
elif page == "Set Savings Goal":
    st.title("Create/Update Savings Goal")
    with st.form("savings_goal_form", clear_on_submit=True):
        tgt = st.number_input("Target Amount (₵)", min_value=0.0, format="%.2f")
        active = st.checkbox("Activate this goal", value=True)
        ok = st.form_submit_button("Save Goal")

    if ok:
        save_data("savings_goals", {"target_amount": tgt, "active": active})
        st.success("Savings goal updated!")
