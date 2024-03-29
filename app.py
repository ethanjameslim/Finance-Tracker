from flask import Flask, redirect, render_template, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import sqlite3
import subprocess
import datetime
import os  
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

#Load Environment Variables (Hashed Password) 
load_dotenv()


app = Flask(__name__)

bcrypt = Bcrypt(app)

app.secret_key = os.urandom(16)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Commonwealth Bank Api --------------------------------------------------------------------------------------------------------------------------------------

api_key = '' #enter your API key here
account_id = ''
seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
url = f'https://secure.api.commbank.com.au/api/cds-au/v1/banking/accounts/{account_id}/transactions?oldest-time={seven_days_ago}'

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

#------------------------------------------------------------------------------------------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User() if int(user_id) == 1 else None

class User(UserMixin):
    # Assuming a single user scenario
    id = 1
    username = "ethanjameslim"  # Replace with your desired username
    password_hash = os.environ.get("HASHED_PASSWORD")

#FUNCTIONS------------------------------------------------------------------------------------------------------------------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect('finance_tracker.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row  #for dictionary-like row objects
    return conn


def checkbudgetexceeded(category, year_month):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch budgets per category
    cursor.execute("SELECT category, amount FROM budgets")
    budgets = {row['category']: row['amount'] for row in cursor.fetchall()}

    # Check if budget exists for the category
    if category in budgets:
        # Check if total spending for that category for that month exceeds the budget
        cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE category = ? AND strftime('%Y-%m', date) = ?", (category, year_month))
        result = cursor.fetchone()
        total_expense = result['total'] if result['total'] is not None else 0
        cursor.close()
        conn.close()

        # Compare total expenses with the budget
        return total_expense > budgets[category]
    else:
        cursor.close()
        conn.close()
        return False  # No budget set for this category

def update_next_due_dates():
    conn = get_db_connection()
    subscriptions = conn.execute('SELECT * FROM subscriptions').fetchall()

    for sub in subscriptions:
        next_due_date = datetime.strptime(sub['next_due'], '%Y-%m-%d')
        if next_due_date < datetime.now():
            if sub['interval'] == 'Monthly':
                new_due_date = next_due_date + relativedelta(months=1)
            elif sub['interval'] == 'Annual':
                new_due_date = next_due_date.replace(year=next_due_date.year + 1)
            
            conn.execute('UPDATE subscriptions SET next_due = ? WHERE sub_id = ?',(new_due_date.strftime('%Y-%m-%d'), sub['sub_id']))
    
    conn.commit()
    conn.close()
        
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#ROUTES---------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.teardown_appcontext
def close_connection(exception):
    conn = get_db_connection()
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
            return redirect("/")  # Redirect to the main page if already logged in
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == User.username and bcrypt.check_password_hash(User.password_hash, password):
            user = User()
            login_user(user)
            return redirect("/")
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        expense_id = request.form.get('delete_button')
        if expense_id:
            expense_id = int(expense_id)  # Convert to integer
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()

    # Fetch categories for dropdown
    cursor.execute("SELECT DISTINCT category FROM expenses")
    categories = [row['category'] for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM budgets")
    budgets = [{row["category"]:row["amount"]} for row in cursor.fetchall()]

    # Build the query based on filters
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    category_filter = request.args.get('category', 'all')
    year_filter = request.args.get('year', '')
    month_filter = request.args.get('month', '')

    if category_filter and category_filter != "all":
        query += " AND category = ?"
        params.append(category_filter)

    if year_filter:
        query += " AND strftime('%Y', date) = ?"
        params.append(year_filter)

    if month_filter:
        query += " AND strftime('%m', date) = ?"
        params.append(month_filter)

    query += " ORDER BY date DESC"

    # Fetch expenses with the current filters
    cursor.execute(query, tuple(params))
    expenses = cursor.fetchall()

    current_date = datetime.now()
    next_month = current_date + timedelta(days=30)  # Adjust based on how you define 'next month'

    # Query to fetch subscriptions due within the next month
    subscriptions = conn.execute('SELECT * FROM subscriptions WHERE next_due BETWEEN ? AND ?',(current_date.strftime('%Y-%m-%d'), next_month.strftime('%Y-%m-%d'))).fetchall()
    
    cursor.close()
    conn.close()

    return render_template("index.html", expenses=expenses, categories=categories, category_filter=category_filter, year_filter=year_filter, month_filter=month_filter, budgets=budgets, subscriptions=subscriptions)



@app.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    formatted_transactions = []  # Initialize an empty list for transactions

    # Common logic for GET and POST to fetch transactions
    if api_key and account_id:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            transactions_data = response.json()['data']['transactions']
            formatted_transactions = [
                {
                    'description': t['description'],
                    'date': datetime.strptime(t['postingDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d'),
                    'amount': t['amount']
                }
                for t in transactions_data
            ]

    if request.method == "POST":
        date = request.form['date']
        category = request.form['category']
        amount = request.form['amount']
        description = request.form['description']

        year_month = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (date, category, amount, description) VALUES (?, ?, ?, ?)", (date, category, amount, description))
        conn.commit()
        cursor.close()
        if checkbudgetexceeded(category, year_month):
            message = f"YOUR BUDGET HAS BEEN EXCEEDED IN THE CATEGORY: {category} IN THE MONTH: {year_month}"
            flash(message, 'warning')
        
        return redirect("/")

    return render_template("addexpense.html", formatted_transactions=formatted_transactions)

@app.route("/set_budget", methods=["GET", "POST"])
@login_required
def update_budget():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch categories for dropdown
    cursor.execute("SELECT DISTINCT category FROM expenses")
    categories = [row['category'] for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM budgets")
    budgets = [{row["category"]:row["amount"]} for row in cursor.fetchall()]
    if request.method == "POST":
        category = request.form['category']
        new_amount = request.form['new_amount']
        if int(new_amount) == 0:
            cursor.execute("DELETE FROM budgets WHERE category = ?", (category,))
        else:
            # First, try to update the budget
            cursor.execute("UPDATE budgets SET amount = ? WHERE category = ?", (new_amount, category))
            
            if cursor.rowcount == 0:
                # No existing budget found, insert a new one
                cursor.execute("INSERT INTO budgets (category, amount) VALUES (?, ?)", (category, new_amount))

        conn.commit()
        cursor.close()
        return redirect("/")
    else:
        return render_template("updatebudget.html", categories=categories, budgets=budgets)

@app.route("/budgetgraph")
@login_required
def budget_graph():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch monthly total spending per category
    cursor.execute("SELECT strftime('%Y-%m', date) as month, category, SUM(amount) as total FROM expenses GROUP BY month, category")
    monthly_category_spending = cursor.fetchall()

    # Transform spending data into a dictionary of dictionaries
    spending_data = {}
    for row in monthly_category_spending:
        month = row['month']
        category = row['category']
        total = row['total']
        if month not in spending_data:
            spending_data[month] = {}
        spending_data[month][category] = total

    # Fetch budgets per category
    cursor.execute("SELECT category, amount FROM budgets")
    budgets = {row['category']: row['amount'] for row in cursor.fetchall()}

    # Prepare data for chart
    months = sorted(list(spending_data.keys()), reverse=True)
    categories = sorted(list(set(budgets.keys())))

    spending_data_formatted = []
    budget_data_formatted = []

    for month in months:
        monthly_spending = []
        monthly_budget = []
        for category in categories:
            monthly_spending.append(spending_data.get(month, {}).get(category, 0))
            monthly_budget.append(budgets.get(category, 0))
        spending_data_formatted.append(monthly_spending)
        budget_data_formatted.append(monthly_budget)

    return render_template("budgetgraph.html", months=months, categories=categories, spending_data=spending_data_formatted, budget_data=budget_data_formatted)

@app.route("/spendingtrend")
@login_required
def spending_trend():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) as total_spending, strftime('%Y-%m', date) as month FROM expenses GROUP BY strftime('%Y-%m', date) ORDER BY month;")
    spending_trend_data = cursor.fetchall()

    months = []
    spending = []

    for row in spending_trend_data:
        months.append(row['month'])
        spending.append(row['total_spending'])

    return render_template('spending_trend.html', months=months, spending=spending)

@app.route("/managesubs", methods=['GET', 'POST'])
@login_required
def managesubscriptions():
    update_next_due_dates()

    conn = get_db_connection()

    # Handle adding a new subscription
    if request.method == 'POST' and 'add_subscription' in request.form:
        name = request.form['name']
        interval = request.form['interval']
        next_due = request.form['next_due']
        notes = request.form['notes']
        conn.execute('INSERT INTO subscriptions (name, interval, next_due, notes) VALUES (?, ?, ?, ?)',
                     (name, interval, next_due, notes))
        conn.commit()

    # Handle deleting a subscription
    if request.method == 'POST' and 'delete_subscription' in request.form:
        sub_id = request.form['delete_subscription']
        conn.execute('DELETE FROM subscriptions WHERE sub_id = ?', (sub_id,))
        conn.commit()

    # Always display current subscriptions
    subscriptions = conn.execute('SELECT * FROM subscriptions').fetchall()
    conn.close()

    return render_template('subscriptions.html', subscriptions=subscriptions)

    

#------------------------------------------------------------------------------------------------------------------------------------------------------------

    

if __name__ == '__main__':
    app.run(debug=True)



