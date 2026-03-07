<<<<<<< HEAD
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
=======
from flask import Flask, render_template, request, redirect, url_for, flash, session
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json

app = Flask(__name__)
app.secret_key = "stocker_secret_2024"

# ================= AWS CONFIGURATION (IAM ROLE) =================

AWS_REGION = "us-east-1"

# Use IAM Role attached to EC2
session_aws = boto3.Session(region_name=AWS_REGION)

# DynamoDB
dynamodb = session_aws.resource('dynamodb')

# SNS
sns = session_aws.client('sns')

# DynamoDB Tables
USER_TABLE = "stocker_users"
STOCK_TABLE = "stocker_stocks"
TRANSACTION_TABLE = "stocker_transactions"
PORTFOLIO_TABLE = "stocker_portfolio"

# SNS Topics
USER_ACCOUNT_TOPIC_ARN = "arn:aws:sns:us-east-1:604665149129:StockerUserAccountTopic"
TRANSACTION_TOPIC_ARN = "arn:aws:sns:us-east-1:604665149129:StockerTransactionTopic"


# ================= HELPER CLASSES =================

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


# ================= SNS FUNCTION =================

def send_notification(topic_arn, subject, message):

    try:

        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )

    except Exception as e:

        print("SNS Error:", e)


# ================= DATABASE FUNCTIONS =================

def get_user_by_email(email):

    table = dynamodb.Table(USER_TABLE)

    response = table.get_item(Key={'email': email})

    return response.get("Item")


def create_user(username, email, password, role):

    table = dynamodb.Table(USER_TABLE)

    user = {

        "id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }

    table.put_item(Item=user)

    return user


def get_all_stocks():

    table = dynamodb.Table(STOCK_TABLE)

    response = table.scan()

    return response.get("Items", [])


def get_stock_by_id(stock_id):

    table = dynamodb.Table(STOCK_TABLE)

    response = table.get_item(Key={'id': stock_id})

    return response.get("Item")


def get_traders():

    table = dynamodb.Table(USER_TABLE)

    response = table.scan(

        FilterExpression=Attr('role').eq("trader")

    )

    return response.get("Items", [])


def get_user_by_id(user_id):

    table = dynamodb.Table(USER_TABLE)

    response = table.scan(

        FilterExpression=Attr('id').eq(user_id)

    )

    users = response.get("Items", [])

    return users[0] if users else None


def get_transactions():

    table = dynamodb.Table(TRANSACTION_TABLE)

    transactions = table.scan().get("Items", [])

    for t in transactions:

        t["user"] = get_user_by_id(t["user_id"])

        t["stock"] = get_stock_by_id(t["stock_id"])

    return transactions


def get_portfolios():

    table = dynamodb.Table(PORTFOLIO_TABLE)

    portfolios = table.scan().get("Items", [])

    for p in portfolios:

        p["user"] = get_user_by_id(p["user_id"])

        p["stock"] = get_stock_by_id(p["stock_id"])

    return portfolios


def get_user_portfolio(user_id):

    table = dynamodb.Table(PORTFOLIO_TABLE)

    response = table.query(

        KeyConditionExpression=Key("user_id").eq(user_id)

    )

    portfolio = response.get("Items", [])

    for p in portfolio:

        p["stock"] = get_stock_by_id(p["stock_id"])

    return portfolio


def get_portfolio_item(user_id, stock_id):

    table = dynamodb.Table(PORTFOLIO_TABLE)

    response = table.get_item(

        Key={

            "user_id": user_id,

            "stock_id": stock_id

        }

    )

    return response.get("Item")


def create_transaction(user_id, stock_id, action, quantity, price):

    table = dynamodb.Table(TRANSACTION_TABLE)

    transaction = {

        "id": str(uuid.uuid4()),

        "user_id": user_id,

        "stock_id": stock_id,

        "action": action,

        "quantity": quantity,

        "price": Decimal(str(price)),

        "status": "completed",

        "transaction_date": datetime.now().isoformat()
    }

    table.put_item(Item=transaction)

    return transaction


def update_portfolio(user_id, stock_id, quantity, average_price):

    table = dynamodb.Table(PORTFOLIO_TABLE)

    quantity = Decimal(str(quantity))

    average_price = Decimal(str(average_price))

    existing = get_portfolio_item(user_id, stock_id)

    if existing and quantity > 0:

        table.update_item(

            Key={"user_id": user_id, "stock_id": stock_id},

            UpdateExpression="set quantity=:q, average_price=:p",

            ExpressionAttributeValues={

                ":q": quantity,

                ":p": average_price
            }
        )

    elif existing and quantity <= 0:

        table.delete_item(

            Key={"user_id": user_id, "stock_id": stock_id}
        )

    elif quantity > 0:

        table.put_item(

            Item={

                "user_id": user_id,

                "stock_id": stock_id,

                "quantity": quantity,

                "average_price": average_price
            }
        )


# ================= ROUTES =================

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        role = request.form["role"]

        user = get_user_by_email(email)

        if user and user["password"] == password and user["role"] == role:

            session["email"] = user["email"]

            session["role"] = user["role"]

            session["user_id"] = user["id"]

            send_notification(

                USER_ACCOUNT_TOPIC_ARN,

                "User Login",

                f"{user['username']} logged in"

            )

            if role == "admin":

                return redirect(url_for("dashboard_admin"))

            else:

                return redirect(url_for("dashboard_trader"))

        flash("Invalid credentials")

    return render_template("login.html")


@app.route('/signup', methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]

        email = request.form["email"]

        password = request.form["password"]

        role = request.form["role"]

        if get_user_by_email(email):

            flash("User already exists")

            return redirect(url_for("login"))

        create_user(username, email, password, role)

        send_notification(

            USER_ACCOUNT_TOPIC_ARN,

            "New User Signup",

            f"{username} created an account"
        )

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route('/dashboard_admin')
def dashboard_admin():

    stocks = get_all_stocks()

    user = get_user_by_email(session["email"])

    return render_template(

        "dashboard_admin.html",

        user=user,

        market_data=stocks
    )


@app.route('/dashboard_trader')
def dashboard_trader():

    stocks = get_all_stocks()

    user = get_user_by_email(session["email"])

    return render_template(

        "dashboard_trader.html",

        user=user,

        market_data=stocks
    )


@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for("index"))


# ================= RUN =================

if __name__ == "__main__":

    app.run(debug=True, host="0.0.0.0", port=5000)
>>>>>>> a11c52c2db9bb42e95c092c8e60ae3e1185a4a52
