import sqlite3
import pandas as pd

# Connect (this will create the file if it doesn’t exist)
conn = sqlite3.connect("exoplanets.db")

# Example: Save a dataframe to SQLite
def save_to_db(df):
    df.to_sql("planets", conn, if_exists="replace", index=False)

def get_from_db():
    return pd.read_sql("SELECT * FROM planets LIMIT 10", conn)
