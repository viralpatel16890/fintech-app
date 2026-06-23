import os
import calendar
import secrets
from contextlib import contextmanager
from datetime import date, datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'finance_dashboard_2026')
DATABASE = os.path.join(os.path.dirname(__file__), 'finance.db')

CATEGORIES = {
    'expense': ['Housing', 'Food', 'Transportation', 'Entertainment', 'Utilities', 'Health', 'Shopping', 'Education', 'Other'],
    'income': ['Salary', 'Freelance', 'Investment', 'Gift', 'Other']
}

CATEGORY_COLORS = {
    'Housing': '#FF6384', 'Food': '#36A2EB', 'Transportation': '#FFCE56',
    'Entertainment': '#4BC0C0', 'Utilities': '#9966FF', 'Health': '#FF9F40',
    'Shopping': '#FF6384', 'Education': '#00BCD4', 'Other': '#9E9E9E',
    'Salary': '#4CAF50', 'Freelance': '#8BC34A', 'Investment': '#00BCD4',
    'Gift': '#E91E63',
}

ALL_CATEGORIES = set(CATEGORIES['expense'] + CATEGORIES['income'])


# ── Database ──────────────────────────────────────────────────────────────────

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE,
                monthly_limit REAL NOT NULL
            )
        ''')
        count = conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
        if count == 0:
            sample_transactions = [
                ('2026-06-01', 'Monthly Salary', 5000.00, 'Salary', 'income'),
                ('2026-06-02', 'Rent Payment', 1200.00, 'Housing', 'expense'),
                ('2026-06-03', 'Weekly Groceries', 85.50, 'Food', 'expense'),
                ('2026-06-05', 'Netflix', 15.99, 'Entertainment', 'expense'),
                ('2026-06-07', 'Electric Bill', 95.00, 'Utilities', 'expense'),
                ('2026-06-10', 'Freelance Project', 750.00, 'Freelance', 'income'),
                ('2026-06-12', 'Restaurant Dinner', 45.20, 'Food', 'expense'),
                ('2026-06-14', 'Gas Station', 52.00, 'Transportation', 'expense'),
                ('2026-06-15', 'Gym Membership', 40.00, 'Health', 'expense'),
                ('2026-06-18', 'Amazon Purchase', 67.99, 'Shopping', 'expense'),
                ('2026-06-20', 'Coffee Shop', 12.50, 'Food', 'expense'),
                ('2026-06-22', 'Internet Bill', 60.00, 'Utilities', 'expense'),
                ('2026-05-01', 'Monthly Salary', 5000.00, 'Salary', 'income'),
                ('2026-05-03', 'Rent Payment', 1200.00, 'Housing', 'expense'),
                ('2026-05-10', 'Groceries', 92.00, 'Food', 'expense'),
                ('2026-05-15', 'Freelance Project', 600.00, 'Freelance', 'income'),
                ('2026-05-18', 'Utilities', 140.00, 'Utilities', 'expense'),
                ('2026-05-22', 'Shopping', 110.00, 'Shopping', 'expense'),
                ('2026-04-01', 'Monthly Salary', 5000.00, 'Salary', 'income'),
                ('2026-04-04', 'Rent Payment', 1200.00, 'Housing', 'expense'),
                ('2026-04-09', 'Groceries', 78.00, 'Food', 'expense'),
                ('2026-04-15', 'Freelance Project', 900.00, 'Freelance', 'income'),
                ('2026-04-20', 'Utilities', 130.00, 'Utilities', 'expense'),
                ('2026-03-01', 'Monthly Salary', 5000.00, 'Salary', 'income'),
                ('2026-03-05', 'Rent Payment', 1200.00, 'Housing', 'expense'),
                ('2026-03-12', 'Groceries', 95.00, 'Food', 'expense'),
                ('2026-03-20', 'Utilities', 145.00, 'Utilities', 'expense'),
                ('2026-02-01', 'Monthly Salary', 5000.00, 'Salary', 'income'),
                ('2026-02-05', 'Rent Payment', 1200.00, 'Housing', 'expense'),
                ('2026-02-14', 'Valentine Dinner', 120.00, 'Food', 'expense'),
                ('2026-01-01', 'Monthly Salary', 5000.00, 'Salary', 'income'),
                ('2026-01-05', 'Rent Payment', 1200.00, 'Housing', 'expense'),
                ('2026-01-10', 'Groceries', 88.00, 'Food', 'expense'),
            ]
            conn.executemany(
                'INSERT INTO transactions (date, description, amount, category, type) VALUES (?, ?, ?, ?, ?)',
                sample_transactions
            )
            sample_budgets = [
                ('Housing', 1300.00), ('Food', 400.00), ('Transportation', 150.00),
                ('Entertainment', 100.00), ('Utilities', 200.00), ('Health', 100.00),
                ('Shopping', 200.00),
            ]
            conn.executemany(
                'INSERT OR IGNORE INTO budgets (category, monthly_limit) VALUES (?, ?)',
                sample_budgets
            )


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        expected_user = os.environ.get('LOGIN_USERNAME', 'admin')
        expected_pass = os.environ.get('LOGIN_PASSWORD', 'changeme')
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user_ok = secrets.compare_digest(username, expected_user)
        pass_ok = secrets.compare_digest(password, expected_pass)
        if user_ok and pass_ok:
            session['logged_in'] = True
            session.permanent = False
            return redirect(url_for('dashboard'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Helpers ───────────────────────────────────────────────────────────────────

def month_start():
    today = date.today()
    return f"{today.year}-{today.month:02d}-01"


def validate_transaction(form):
    errors = []
    txn_date = form.get('date', '').strip()
    description = form.get('description', '').strip()
    raw_amount = form.get('amount', '').strip()
    category = form.get('category', '').strip()
    txn_type = form.get('type', '').strip()

    if not txn_date:
        errors.append('Date is required.')
    else:
        try:
            datetime.strptime(txn_date, '%Y-%m-%d')
        except ValueError:
            errors.append('Date must be in YYYY-MM-DD format.')

    if not description:
        errors.append('Description is required.')
    elif len(description) > 100:
        errors.append('Description must be 100 characters or fewer.')

    if not raw_amount:
        errors.append('Amount is required.')
    else:
        try:
            amount = float(raw_amount)
            if amount <= 0:
                errors.append('Amount must be greater than zero.')
        except ValueError:
            errors.append('Amount must be a valid number.')

    if txn_type not in ('income', 'expense'):
        errors.append('Transaction type must be income or expense.')

    if category not in ALL_CATEGORIES:
        errors.append('Invalid category selected.')
    elif txn_type in ('income', 'expense'):
        if category not in CATEGORIES.get(txn_type, []):
            errors.append(f'Category "{category}" is not valid for {txn_type} transactions.')

    return errors


def validate_budget(form):
    errors = []
    category = form.get('category', '').strip()
    raw_limit = form.get('limit', '').strip()

    if category not in CATEGORIES['expense']:
        errors.append('Invalid expense category.')

    if not raw_limit:
        errors.append('Monthly limit is required.')
    else:
        try:
            limit = float(raw_limit)
            if limit <= 0:
                errors.append('Monthly limit must be greater than zero.')
        except ValueError:
            errors.append('Monthly limit must be a valid number.')

    return errors


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    ms = month_start()
    today = date.today()

    with get_db() as conn:
        total_income = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND date>=?", (ms,)
        ).fetchone()[0]
        total_expenses = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND date>=?", (ms,)
        ).fetchone()[0]
        balance = total_income - total_expenses
        savings_rate = round((balance / total_income * 100) if total_income > 0 else 0, 1)

        recent = conn.execute(
            "SELECT * FROM transactions ORDER BY date DESC LIMIT 6"
        ).fetchall()

        category_data = [
            (row['category'], round(row['total'], 2))
            for row in conn.execute(
                "SELECT category, SUM(amount) as total FROM transactions WHERE type='expense' AND date>=? GROUP BY category ORDER BY total DESC",
                (ms,)
            ).fetchall()
        ]

        monthly_trend = []
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            month_str = f"{y}-{m:02d}"
            inc = conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND strftime('%Y-%m',date)=?",
                (month_str,)
            ).fetchone()[0]
            exp = conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND strftime('%Y-%m',date)=?",
                (month_str,)
            ).fetchone()[0]
            monthly_trend.append({'month': calendar.month_abbr[m], 'income': round(inc, 2), 'expenses': round(exp, 2)})

        budgets = conn.execute('SELECT * FROM budgets').fetchall()
        budget_status = []
        for b in budgets:
            spent = conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND category=? AND date>=?",
                (b['category'], ms)
            ).fetchone()[0]
            pct = min(round((spent / b['monthly_limit'] * 100) if b['monthly_limit'] > 0 else 0, 1), 100)
            budget_status.append({
                'category': b['category'], 'limit': b['monthly_limit'],
                'spent': round(spent, 2), 'remaining': round(max(b['monthly_limit'] - spent, 0), 2),
                'percent': pct
            })

    return render_template('dashboard.html',
        total_income=total_income, total_expenses=total_expenses,
        balance=balance, savings_rate=savings_rate,
        recent=recent, category_data=category_data,
        monthly_trend=monthly_trend, budget_status=budget_status,
        category_colors=CATEGORY_COLORS
    )


@app.route('/transactions')
@login_required
def transactions():
    filter_type = request.args.get('type', 'all')
    filter_category = request.args.get('category', 'all')

    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if filter_type != 'all':
        query += " AND type=?"
        params.append(filter_type)
    if filter_category != 'all':
        query += " AND category=?"
        params.append(filter_category)
    query += " ORDER BY date DESC"

    with get_db() as conn:
        txns = conn.execute(query, params).fetchall()
        categories = conn.execute("SELECT DISTINCT category FROM transactions ORDER BY category").fetchall()

    total = sum(t['amount'] * (1 if t['type'] == 'income' else -1) for t in txns)
    return render_template('transactions.html',
        transactions=txns, categories=categories,
        filter_type=filter_type, filter_category=filter_category,
        total=round(total, 2)
    )


@app.route('/transactions/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        errors = validate_transaction(request.form)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('add_transaction.html', categories=CATEGORIES,
                                   today=date.today().isoformat(), form=request.form)
        with get_db() as conn:
            conn.execute(
                "INSERT INTO transactions (date, description, amount, category, type) VALUES (?,?,?,?,?)",
                (request.form['date'].strip(), request.form['description'].strip(),
                 float(request.form['amount']), request.form['category'], request.form['type'])
            )
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('transactions'))
    return render_template('add_transaction.html', categories=CATEGORIES,
                           today=date.today().isoformat(), form={})


@app.route('/transactions/delete/<int:txn_id>', methods=['POST'])
@login_required
def delete_transaction(txn_id):
    with get_db() as conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
    flash('Transaction deleted.', 'warning')
    return redirect(url_for('transactions'))


@app.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    if request.method == 'POST':
        errors = validate_budget(request.form)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return redirect(url_for('budgets'))
        with get_db() as conn:
            conn.execute(
                "INSERT INTO budgets (category, monthly_limit) VALUES (?,?) ON CONFLICT(category) DO UPDATE SET monthly_limit=?",
                (request.form['category'], float(request.form['limit']), float(request.form['limit']))
            )
        flash('Budget saved!', 'success')
        return redirect(url_for('budgets'))

    ms = month_start()
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM budgets ORDER BY category').fetchall()
        budget_data = []
        for b in rows:
            spent = conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND category=? AND date>=?",
                (b['category'], ms)
            ).fetchone()[0]
            pct = min(round((spent / b['monthly_limit'] * 100) if b['monthly_limit'] > 0 else 0, 1), 100)
            budget_data.append({
                'id': b['id'], 'category': b['category'], 'limit': b['monthly_limit'],
                'spent': round(spent, 2), 'remaining': round(max(b['monthly_limit'] - spent, 0), 2),
                'percent': pct
            })
    return render_template('budgets.html', budgets=budget_data, expense_categories=CATEGORIES['expense'])


@app.route('/budgets/delete/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    with get_db() as conn:
        conn.execute("DELETE FROM budgets WHERE id=?", (budget_id,))
    flash('Budget removed.', 'warning')
    return redirect(url_for('budgets'))


init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
