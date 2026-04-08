from flask import Flask, redirect, render_template, request, session
from flask_wtf.csrf import CSRFProtect
import sqlite3
from dotenv import load_dotenv
import os
from pathlib import Path
from openai import OpenAI
import json
from bcrypt import hashpw, gensalt, checkpw 

load_dotenv(Path(__file__).parent / '.env')
openai_api_key = os.getenv('OPENAI_API_KEY')
secret_key = os.getenv('SECRET_KEY')
client = OpenAI(api_key=openai_api_key)
print("Environment variables loaded successfully!") 


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
csrf = CSRFProtect(app)
@app.route('/', methods=['GET'])
def form():
    if 'email' not in session:
      return redirect('/login')
    return render_template('forms.html')
   

@app.route('/submit-profile', methods=['POST'])
def submit_form():
    if 'email' not in session:
        return redirect('/login')
    print("Form was submitted!")

    
    full_name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    career = request.form.get('career')
    role = request.form.get('role')

    
    if len(full_name) < 2 or len(full_name) > 100:
        print("Name validation failed!")
        return render_template('forms.html', error='Invalid name.')
    elif '@' not in email or len(email) < 6 or len(email) > 50:
        print("Email validation failed!")   
        return render_template('forms.html', error='Invalid email address.')
    elif len(phone) < 10 or len(phone) > 15:
        print("Phone validation failed!")
        return render_template('forms.html', error='Invalid phone number.')


    print(f'Name: {full_name}')
    print(f'Email: {email}')
    print(f'Phone: {phone}')
    print(f'Career: {career}')
    print(f'Role: {role}')


    conn = sqlite3.connect('networking.db')
    cursor = conn.cursor()
    cursor.execute( 'CREATE TABLE IF NOT EXISTS profiles (name, email, phone, career, role)')
    cursor.execute('INSERT INTO profiles (name, email, phone, career, role) VALUES (?, ?, ?, ?, ?)', (full_name, email, phone, career, role))
    conn.commit()
    conn.close()
    
   
    prompt = (f'Write a short summary and networking tip for someone who works in {career} as a {role}. Return as JSON with keys "summary" and "tip".')
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    result = response.choices[0].message.content
    print(f"AI returned: {result}")
    result = result.strip().removeprefix('```json').removesuffix('```').strip()
    
    data = json.loads(result)
    summary = data['summary']
    tip = data['tip']
    return render_template('results.html', summary=summary, tip=tip)
   
@app.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashpw(password.encode('utf-8'), gensalt())
   
        if len(username) < 3 or len(username) > 30:
            print("Username validation failed!")
            return render_template('registration.html', error='Invalid username.')  
        elif len(password) < 6 or len(password) > 100:
            print("Password validation failed!")
            return render_template('registration.html', error='Invalid password.')  
        elif'@' not in email or len(email) < 6 or len(email) > 50:
            print("Email validation failed!")   
            return render_template('registration.html', error='Invalid email address.') 

        print(f'Email: {email}')
        print(f'Username: {username}')  
        conn = sqlite3.connect('networking.db')
        cursor = conn.cursor()
        conn.execute( 'CREATE TABLE IF NOT EXISTS users (id, email, username, password)')
        conn.execute('INSERT INTO users (id, email, username, password) VALUES (?, ?, ?, ?)', (None, email, username, hashed_password))
        conn.commit()
        conn.close()
        print ("Registration Successful!")
        return redirect('/login')

    return render_template('registration.html')  
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('networking.db')
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        print(f"DB result: {result}")
        conn.close()

        if result and checkpw(password.encode('utf-8'), result[0]):
            print("Login successful!")
            session['email'] = email
            return redirect('/')
        else:
            print("Login failed!")
            return render_template('login.html', error='Invalid email or password.')

    return render_template('login.html')



