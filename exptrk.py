import streamlit as st
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Initialize the database
def initialize_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    conn.commit()
    conn.close()

# List of predefined categories
categories = ["Food", "Transportation", "Entertainment", "Utilities", "Rent", "Miscellaneous"]

# Initialize database
initialize_db()

# Streamlit UI
st.title("Expense Tracker")

# Session state for logged-in user
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

def register_user(username, password):
    if username and password:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            st.success("User registered successfully")
        except sqlite3.IntegrityError:
            st.error("Username already exists")
        conn.close()
    else:
        st.error("Please fill all the fields")

def login_user(username, password):
    if username and password:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            st.session_state.logged_in_user = user[0]
            st.success("Logged in successfully")
            # Create a new table for the user if it does not exist
            create_user_expenses_table(user[0])
        else:
            st.error("Invalid username or password")
    else:
        st.error("Please fill all the fields")

def create_user_expenses_table(user_id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    table_name = f"expenses_{user_id}"
    c.execute(f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def add_expense(user_id, category, description, amount):
    date = datetime.now().strftime('%Y-%m-%d')
    table_name = f"expenses_{user_id}"
    if category and amount:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute(f"INSERT INTO {table_name} (date, category, description, amount) VALUES (?, ?, ?, ?)",
                  (date, category, description, amount))
        conn.commit()
        
        # Check if the budget for the category is exceeded
        c.execute(f"SELECT SUM(amount) FROM {table_name} WHERE category=?", (category,))
        total_spent = c.fetchone()[0]
        c.execute("SELECT amount FROM budgets WHERE user_id=? AND category=?", (user_id, category))
        budget = c.fetchone()
        if budget and total_spent > budget[0]:
            st.warning(f"Warning: You have exceeded your budget for {category}!")
        
        conn.close()
        st.success("Expense added successfully")
    else:
        st.error("Please fill all the required fields")

def view_expenses(user_id):
    table_name = f"expenses_{user_id}"
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name}")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_expense(user_id, expense_id):
    table_name = f"expenses_{user_id}"
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute(f"DELETE FROM {table_name} WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()
    st.success("Expense deleted successfully")


def refresh_categories():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("SELECT * FROM categories")
    categories = c.fetchall()
    conn.close()
    return categories

def set_budget(user_id, category, amount):
    if category and amount:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute("INSERT INTO budgets (user_id, category, amount) VALUES (?, ?, ?)",
                  (user_id, category, amount))
        conn.commit()
        conn.close()
        st.success("Budget set successfully")
    else:
        st.error("Please fill all the required fields")

def generate_expense_report(user_id):
    table_name = f"expenses_{user_id}"
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute(f"SELECT category, SUM(amount) FROM {table_name} GROUP BY category")
    data = c.fetchall()
    conn.close()
    
    if data:
        df = pd.DataFrame(data, columns=['Category', 'Amount'])
        fig, ax = plt.subplots()
        ax.pie(df['Amount'], labels=df['Category'], autopct='%1.1f%%', startangle=140)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.title('Expense Report')
        st.pyplot(fig)
    else:
        st.info("No expenses to report")

# User Authentication
if st.session_state.logged_in_user is None:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        login_user(username, password)
    
    st.subheader("Register")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    if st.button("Register"):
        register_user(new_username, new_password)

else:
    # Main Application
    st.subheader("Add Expense")
    selected_category = st.selectbox("Category", categories)
    description = st.text_input("Description")
    amount = st.number_input("Amount", min_value=0.01)
    if st.button("Add Expense"):
        add_expense(st.session_state.logged_in_user, selected_category, description, amount)
    
    st.subheader("View Expenses")
    expenses = view_expenses(st.session_state.logged_in_user)
    if expenses:
        df = pd.DataFrame(expenses, columns=['ID', 'Date', 'Category', 'Description', 'Amount'])
        st.table(df)
        selected_expense_id = st.selectbox("Select Expense to Delete", df['ID'])
        if st.button("Delete Expense"):
            delete_expense(st.session_state.logged_in_user, selected_expense_id)
    else:
        st.info("No expenses found")
    
    st.subheader("Set Budget")
    budget_category = st.selectbox("Budget Category", categories)
    budget_amount = st.number_input("Budget Amount", min_value=0.01)
    if st.button("Set Budget"):
        set_budget(st.session_state.logged_in_user, budget_category, budget_amount)
    
    st.subheader("Generate Expense Report")
    if st.button("Generate Report"):
        generate_expense_report(st.session_state.logged_in_user)
