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
    looking_for TEXT,
    summary TEXT,
    tip TEXT
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    username TEXT,
    password TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_email TEXT,
    user2_email TEXT,
    match TEXT,
    reason TEXT,
    confidence TEXT
)''')

conn.commit()
conn.close()


