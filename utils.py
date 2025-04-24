import os
import json
import datetime
import pandas as pd
import streamlit as st

# Data loading and saving functions
def load_data():
    """Load financial data from JSON file, or initialize if it doesn't exist"""
    if os.path.exists('finance_data.json'):
        try:
            with open('finance_data.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return initialize_data()
    else:
        return initialize_data()

def save_data(data):
    """Save financial data to JSON file"""
    try:
        with open('finance_data.json', 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

def initialize_data():
    """Initialize empty data structure"""
    return {
        'income': [],
        'expenses': [],
        'budget': [],
        'savings': [],
        'investments': [],
        'savings_goals': []
    }

# Calculation functions
def calculate_monthly_income(data, month, year):
    """Calculate total income for a given month and year"""
    total = 0
    for entry in data.get('income', []):
        entry_date = datetime.datetime.strptime(entry['date'], '%Y-%m-%d')
        if entry_date.month == month and entry_date.year == year:
            total += entry['amount']
    return total

def calculate_monthly_expenses(data, month, year):
    """Calculate total expenses for a given month and year"""
    total = 0
    for entry in data.get('expenses', []):
        entry_date = datetime.datetime.strptime(entry['date'], '%Y-%m-%d')
        if entry_date.month == month and entry_date.year == year:
            total += entry['amount']
    return total

def calculate_monthly_savings(data, month, year):
    """Calculate total savings for a given month and year"""
    total = 0
    for entry in data.get('savings', []):
        entry_date = datetime.datetime.strptime(entry['date'], '%Y-%m-%d')
        if entry_date.month == month and entry_date.year == year:
            total += entry['amount']
    return total

def calculate_budget_vs_actual(data, month, year):
    """Calculate the difference between budget and actual expenses for a given month and year"""
    # Get total budget for the month
    total_budget = 0
    for entry in data.get('budget', []):
        if entry['month'] == month and entry['year'] == year:
            total_budget += entry['amount']
    
    # Get total expenses for the month
    total_expenses = calculate_monthly_expenses(data, month, year)
    
    # Return the difference (positive means under budget, negative means over budget)
    return total_budget - total_expenses

def get_expense_categories():
    """Return a list of standard expense categories"""
    return [
        "Housing", "Utilities", "Groceries", "Transportation", 
        "Dining Out", "Entertainment", "Shopping", "Healthcare", 
        "Education", "Personal Care", "Travel", "Gifts", 
        "Subscriptions", "Insurance", "Taxes", "Debt Payments", "Other"
    ]

def get_income_categories():
    """Return a list of standard income categories"""
    return [
        "Salary", "Freelance", "Business", "Investments", 
        "Dividends", "Interest", "Rental Income", "Gifts Received", 
        "Tax Refunds", "Other"
    ]

def get_month_year_range(months_back=12):
    """Get a list of month-year tuples for dropdown menus, from current month going back"""
    today = datetime.datetime.now()
    month_year_list = []
    
    for i in range(months_back):
        date = today - datetime.timedelta(days=30*i)
        month_year = (date.month, date.year, date.strftime("%B %Y"))
        month_year_list.append(month_year)
    
    return month_year_list
