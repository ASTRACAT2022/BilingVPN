import os
import sqlite3
import random
import string
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, g

app = Flask(__name__)
app.secret_key = 'supersecretkey123'
DATABASE = 'billing.db'

# Генерация случайного кода транзакции
def generate_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# Инициализация БД
def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                amount INTEGER,
                donation_status TEXT,
                user_wallet TEXT,
                custom_sni TEXT,
                order_status TEXT,
                config_link TEXT,
                created_at DATETIME,
                confirmed_at DATETIME,
                completed_at DATETIME
            )
        ''')
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

init_db()

# Стили и шаблоны
common_style = '''
<style>
    :root { --primary: #7928CA; --secondary: #FF0080; --dark: #0a0a0a; }
    * { box-sizing: border-box; margin: 0; font-family: 'Inter', sans-serif; }
    body { background: var(--dark); color: white; }
    .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
    .card { background: #1a1a1a; border-radius: 12px; padding: 2rem; margin: 2rem 0; }
    .gradient-text { background: linear-gradient(45deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .btn { background: linear-gradient(45deg, var(--primary), var(--secondary)); color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block; transition: transform 0.2s; }
    .btn:hover { transform: translateY(-2px); }
    table { width: 100%; border-collapse: collapse; margin: 2rem 0; }
    th, td { padding: 1rem; text-align: left; border-bottom: 1px solid #333; }
</style>
'''

home_template = common_style + '''
<div class="container">
    <h1 class="gradient-text">Xray VPN Service</h1>
    <div class="card">
        <h2>Инструкция по подключению:</h2>
        <p>1. Приобретите подписку</p>
        <p>2. После подтверждения платежа получите конфиг</p>
        <p>3. Настройте Xray клиент по инструкции ниже</p>
        <a href="/buy" class="btn">Купить подписку - 75₽/мес</a>
    </div>
    
    <div class="card">
        <h2>Настройка клиента Xray</h2>
        <pre><code>{
  "inbounds": [...],
  "outbounds": [...]
}</code></pre>
    </div>
</div>
'''

purchase_template = common_style + '''
<div class="container">
    <h1 class="gradient-text">Оформление подписки</h1>
    <div class="card">
        <h2>Ваш код транзакции: <span style="color: #FF0080">{{ code }}</span></h2>
        <p>1. Перейдите на <a href="https://www.donationalerts.com/r/astracatinc" target="_blank" style="color: #7928CA">DonationAlerts</a></p>
        <p>2. Укажите сумму 75₽</p>
        <p>3. В комментарии укажите код: <strong>{{ code }}</strong></p>
        <p>После подтверждения платежа администратором (до 5 дней), вы сможете получить конфиг.</p>
        <a href="/order/{{ code }}" class="btn">Проверить статус</a>
    </div>
</div>
'''

order_template = common_style + '''
<div class="container">
    <h1 class="gradient-text">Статус заказа: {{ transaction["code"] }}</h1>
    <div class="card">
        {% if transaction["donation_status"] == "confirmed" %}
            <h2>✅ Платеж подтвержден!</h2>
            {% if not transaction["user_wallet"] %}
                <form method="POST">
                    <input type="text" name="wallet" placeholder="Ваш кошелек" required>
                    <input type="text" name="sni" placeholder="Кастомный SNI (опционально)">
                    <button type="submit" class="btn">Отправить данные</button>
                </form>
            {% elif transaction["order_status"] == "completed" %}
                <a href="{{ transaction['config_link'] }}" class="btn">Скачать конфиг</a>
            {% else %}
                <p>Статус заказа: {{ transaction["order_status"] }} ⏳</p>
            {% endif %}
        {% else %}
            <h2>⏳ Ожидание подтверждения платежа</h2>
            <p>Проверяем статус каждые 5 минут...</p>
        {% endif %}
    </div>
</div>
'''

admin_template = common_style + '''
<div class="container">
    <h1 class="gradient-text">Админ панель</h1>
    <table>
        <tr>
            <th>Код</th>
            <th>Статус</th>
            <th>Кошелек</th>
            <th>SNI</th>
            <th>Действия</th>
        </tr>
        {% for t in transactions %}
        <tr>
            <td>{{ t["code"] }}</td>
            <td>{{ t["donation_status"] }}</td>
            <td>{{ t["user_wallet"] or '—' }}</td>
            <td>{{ t["custom_sni"] or '—' }}</td>
            <td>
                {% if t["donation_status"] == "pending" %}
                    <a href="/admin/confirm/{{ t['code'] }}" class="btn">Подтвердить</a>
                {% elif t["order_status"] != "completed" %}
                    <form method="POST" action="/admin/complete/{{ t['code'] }}">
                        <input type="text" name="config_link" placeholder="Ссылка на конфиг" required>
                        <button type="submit" class="btn">Завершить</button>
                    </form>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
'''

# Роуты
@app.route('/')
def index():
    return render_template_string(home_template)

@app.route('/buy')
def buy():
    code = generate_code()
    db = get_db()
    db.execute('INSERT INTO transactions (code, amount, donation_status, created_at) VALUES (?, ?, ?, ?)',
              (code, 75, 'pending', datetime.now()))
    db.commit()
    return render_template_string(purchase_template, code=code)

@app.route('/order/<code>', methods=['GET', 'POST'])
def order(code):
    db = get_db()
    if request.method == 'POST':
        db.execute('UPDATE transactions SET user_wallet = ?, custom_sni = ? WHERE code = ?',
                  (request.form['wallet'], request.form.get('sni'), code))
        db.commit()
    
    t = db.execute('SELECT * FROM transactions WHERE code = ?', (code,)).fetchone()
    return render_template_string(order_template, transaction=t)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form['password'] == 'admin123':
            session['admin'] = True
            return redirect('/admin/dashboard')
    return render_template_string(admin_template)

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect('/admin')
    
    db = get_db()
    transactions = db.execute('SELECT * FROM transactions').fetchall()
    return render_template_string(admin_template, transactions=transactions)

@app.route('/admin/confirm/<code>')
def confirm(code):
    if not session.get('admin'):
        return redirect('/admin')
    
    db = get_db()
    db.execute('UPDATE transactions SET donation_status = "confirmed" WHERE code = ?', (code,))
    db.commit()
    return redirect('/admin/dashboard')

@app.route('/admin/complete/<code>', methods=['POST'])
def complete(code):
    if not session.get('admin'):
        return redirect('/admin')
    
    db = get_db()
    db.execute('UPDATE transactions SET order_status = "completed", config_link = ? WHERE code = ?',
              (request.form['config_link'], code))
    db.commit()
    return redirect('/admin/dashboard')

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5000, debug=True)
