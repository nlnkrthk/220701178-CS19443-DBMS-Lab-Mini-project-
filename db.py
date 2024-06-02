import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import ttk

# Function to get the structure of each table and return it as a DataFrame
def get_table_structure(table_name, cursor):
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    column_names = ["Column ID", "Name", "Type", "Not Null", "Default Value", "Primary Key"]
    df = pd.DataFrame(columns, columns=column_names)
    return df

# Connect to the SQLite database
conn = sqlite3.connect('expenses.db')
c = conn.cursor()

# Fetch the names of all tables in the database
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()

# Tkinter setup
root = tk.Tk()
root.title("SQLite Database Table Structures")
root.configure(bg="white")

# Display the structure of each table
for table in tables:
    table_name = table[0]

    # Create a frame for each table
    frame = tk.Frame(root, bg="white")
    frame.pack(padx=10, pady=10, fill="both", expand=True)

    # Table title
    title = tk.Label(frame, text=f"Structure of table: {table_name}", bg="white", font=("Helvetica", 16, "bold"))
    title.pack(pady=5)

    # Fetch the table structure
    df = get_table_structure(table_name, c)

    # Create a treeview to display the table structure
    tree = ttk.Treeview(frame)
    tree["columns"] = list(df.columns)
    tree["show"] = "headings"

    # Define the column headings and set the column width
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")

    # Insert the data into the treeview
    for index, row in df.iterrows():
        tree.insert("", "end", values=list(row))

    # Add the treeview to the frame
    tree.pack(fill="both", expand=True)

    # Apply a white background to the treeview
    style = ttk.Style()
    style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
    style.configure("Treeview.Heading", background="white", foreground="black")

# Close the connection
conn.close()

# Run the Tkinter main loop
root.mainloop()
