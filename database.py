import sqlite3

conn = sqlite3.connect('networking.db')
cursor = conn.cursor()
cursor.execute( 'CREATE TABLE IF NOT EXISTS profiles (name, email, phone, career, role)')
cursor.execute( 'CREATE TABLE IF NOT EXISTS profiles (id, email, username, password)')
conn.commit()
conn.close()


