import sqlite3

conn = sqlite3.connect('networking.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    career TEXT,
    role TEXT,
    industry TEXT,
    looking_for TEXT
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    username TEXT,
    password TEXT
)''')
conn.commit()
conn.close()


