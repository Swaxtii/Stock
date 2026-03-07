from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config
import bcrypt
import boto3
import uuid
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# ---- HOME PAGE ----
@app.route('/')
def home():
    return render_template('home.html')

# ---- REGISTER ----
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        session['user'] = {'username': username, 'email': email, 'balance': 10000}
        session['transactions'] = []
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')

# ---- LOGIN ----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        session['user'] = {'username': 'TestUser', 'email': email, 'balance': 10000}
        session['transactions'] = []
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# ---- DASHBOARD ----
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

# ---- TRADE ----
@app.route('/trade', methods=['GET', 'POST'])
def trade():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        symbol = request.form['symbol']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        action = request.form['action']
        total = price * quantity

        companies = {
            'AAPL': 'Apple Inc.', 'GOOGL': 'Alphabet Inc.',
            'MSFT': 'Microsoft Corp.', 'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.', 'META': 'Meta Platforms'
        }

        if action == 'buy':
            if session['user']['balance'] >= total:
                session['user']['balance'] -= total
                if 'transactions' not in session:
                    session['transactions'] = []
                session['transactions'].append({
                    'action': 'buy',
                    'symbol': symbol,
                    'company': companies.get(symbol, symbol),
                    'quantity': quantity,
                    'price': price,
                    'total': round(total, 2),
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
                session.modified = True
                flash(f'Successfully bought {quantity} shares of {symbol} for ${total:.2f}!', 'success')
            else:
                flash('Insufficient balance!', 'danger')

        elif action == 'sell':
            session['user']['balance'] += total
            if 'transactions' not in session:
                session['transactions'] = []
            session['transactions'].append({
                'action': 'sell',
                'symbol': symbol,
                'company': companies.get(symbol, symbol),
                'quantity': quantity,
                'price': price,
                'total': round(total, 2),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M')
            })
            session.modified = True
            flash(f'Successfully sold {quantity} shares of {symbol} for ${total:.2f}!', 'success')

        return redirect(url_for('trade'))

    return render_template('trade.html', user=session['user'])

# ---- PORTFOLIO ----
@app.route('/portfolio')
def portfolio():
    if 'user' not in session:
        return redirect(url_for('login'))

    transactions = session.get('transactions', [])
    holdings = {}

    for tx in transactions:
        symbol = tx['symbol']
        if symbol not in holdings:
            holdings[symbol] = {
                'symbol': symbol,
                'company': tx['company'],
                'quantity': 0,
                'total_cost': 0,
                'current_price': tx['price']
            }
        if tx['action'] == 'buy':
            holdings[symbol]['quantity'] += tx['quantity']
            holdings[symbol]['total_cost'] += tx['total']
        elif tx['action'] == 'sell':
            holdings[symbol]['quantity'] -= tx['quantity']
            holdings[symbol]['total_cost'] -= tx['total']

    portfolio = []
    total_value = 0

    for symbol, data in holdings.items():
        if data['quantity'] > 0:
            avg_price = data['total_cost'] / data['quantity']
            total_val = data['quantity'] * data['current_price']
            profit = total_val - data['total_cost']
            total_value += total_val
            portfolio.append({
                'symbol': symbol,
                'company': data['company'],
                'quantity': data['quantity'],
                'avg_price': round(avg_price, 2),
                'current_price': data['current_price'],
                'total_value': round(total_val, 2),
                'profit': round(profit, 2)
            })

    return render_template('portfolio.html',
                           user=session['user'],
                           portfolio=portfolio,
                           transactions=transactions,
                           total_value=round(total_value, 2))

# ---- LOGOUT ----
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
