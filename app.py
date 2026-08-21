from urllib import response

from flask import Flask, redirect, render_template, request, session
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
from dotenv import load_dotenv
import os
from pathlib import Path
from openai import OpenAI
import json
from bcrypt import hashpw, gensalt, checkpw 
from datetime import timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv(Path(__file__).parent / '.env')
openai_api_key = os.getenv('OPENAI_API_KEY')
secret_key = os.getenv('SECRET_KEY')
sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
client = OpenAI(api_key=openai_api_key)
print("Environment variables loaded successfully!") 


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
csrf = CSRFProtect(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

def send_email(to_email, match_name, match_career, match_reason):
    message = Mail( 
        from_email=os.getenv('SENDER_EMAIL'),
        to_emails=to_email,
        subject='You have a new match on NetWorth! 🤝',
        html_content=f'''
        <h2>You matched with {match_name}!</h2>
        <p><strong>Why you matched:</strong> {match_reason}</p>
        <p><strong>Their career:</strong> {match_career}</p>
        <p>Don't let this connection go cold — reach out and grab a coffee or hop on a Zoom!</p>
        <a href="https://neworking-app.onrender.com/matches">View your matches</a>
        '''
    )
    try:
        sendgrid = SendGridAPIClient(os.geenv('SENDGRID_API_KEY'))
        sendgrid.send(message)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Email error: {e}")
        

@app.route('/')
def landing():
   return render_template('landing.html')
   

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
    industry = request.form.get('industry')
    looking_for = request.form.get('looking_for')
   


    
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


    
   
    prompt = (f'Write a short summary and networking tip for {full_name} who works in {career} as a {role} in the {industry} industry looking for {looking_for}. '
          f'They are attending a professional networking event in the Bay Area. '
          f'The tip should be specific to their role as a {role} and their goal of finding {looking_for}, not generic advice. '
          f'Write in a warm, encouraging, human tone. '
          f'Return as JSON with keys "summary" and "tip".')
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

    conn = sqlite3.connect('networking.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO profiles (name, email, phone, career, role, industry, looking_for, summary, tip) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (full_name, email, phone, career, role, industry, looking_for, summary, tip))
    conn.commit()
    conn.close()
        
    
    return render_template('results.html', summary=summary, tip=tip)
   
@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
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
        session['email'] = email
        session.permanent = True
        return redirect('/profile')

    return render_template('registration.html')  
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
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
            session.permanent = True
            return redirect('/profile')
        else:
            print("Login failed!")
            return render_template('login.html', error='Invalid email or password.')

    return render_template('login.html')


@app.route('/profile', methods=['GET'])
def profile():
    if 'email' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('networking.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, email, phone, career, role, industry, looking_for FROM profiles WHERE email = ?', (session['email'],))
    user_profile = cursor.fetchone()
    conn.close()
    if user_profile:
        return render_template('profile.html', profile=user_profile)
    else:
        return render_template('forms.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/matches')
def matches():
    if 'email' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('networking.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, email, phone, career, role, industry, looking_for FROM profiles WHERE email = ?', (session['email'],))
    current_user = cursor.fetchone() 
    cursor.execute('SELECT name, email, phone, career, role, industry, looking_for FROM profiles WHERE email != ?', (session['email'],))

    all_profiles = cursor.fetchall()

    cursor.execute('SELECT user1_email, user2_email, match, reason FROM matches WHERE user1_email = ? OR user2_email = ?', (session['email'], session['email']))
    existing_matches = cursor.fetchall()
   

    if existing_matches:
        matches_result = []
        for em in existing_matches:
            cursor.execute('SELECT name, email, phone, career, role, industry, looking_for FROM profiles WHERE email = ?', (em[1],))
            profile = cursor.fetchone()
            matches_result.append({
                'profile': profile,
                'match': em[2],
                'reason': em[3]
            })
        conn.close()
        return render_template('matches.html', matches=matches_result)

    matches_result = []
    for profile in all_profiles:
        prompt = f"""You are a strict professional networking matchmaker. Be skeptical — only recommend a match if there is a clear, specific reason these two people would benefit from connecting.

Person 1: {current_user[0]}, works in {current_user[3]} as {current_user[4]}, industry: {current_user[5]}, looking for: {current_user[6]}
Person 2: {profile[0]}, works in {profile[3]} as {profile[4]}, industry: {profile[5]}, looking for: {profile[6]}

A good match requires complementary intent — for example, one person offering what the other is looking for, shared industry with different specialties, or a clear mentor/mentee fit. Two people who both want the same thing (e.g. both seeking mentors) are NOT a good match.

Return JSON with keys "match" (yes or no), "reason" (one specific sentence), and "confidence" (a number 1-10)and "suggestion" (one sentence recommending coffee or Zoom and what to discuss)."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content
            result = result.strip().removeprefix('```json').removesuffix('```').strip()
            data = json.loads(result)
            matches_result.append({
                'profile': profile,
                'match': data['match'],
                'reason': data['reason'],
                'confidence': data['confidence'],
                'suggestion': data['suggestion']
            })

            cursor.execute('INSERT INTO matches (user1_email, user2_email, match, reason, confidence) VALUES (?, ?, ?, ?, ?, ?)',
            (session['email'], profile[1], data['match'], data['reason'], data['confidence'], data['suggestion']))
            send_email(
                session['email'],
                profile[0],
                profile[3],
                data['reason']
                )
            
        except Exception as e:
            print(f"Match error for {profile[0]}: {e}")
            matches_result.append({
                'profile': profile,
                'match': 'unknown',
                'reason': 'Could not generate match at this time.',
                'confidence': 'N/A',
                'suggestion': 'Could not generate suggestion at this time.'

            })

    conn.commit()
    conn.close()

    return render_template('matches.html', matches=matches_result)
def init_db():
    conn = sqlite3.connect('networking.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, phone TEXT,
        career TEXT, role TEXT, industry TEXT, looking_for TEXT,
        summary TEXT, tip TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT, username TEXT, password TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_email TEXT, user2_email TEXT,
        match TEXT, reason TEXT, confidence TEXT, suggestion TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

if __name__ == '__main__':
    app.run(debug=True)
