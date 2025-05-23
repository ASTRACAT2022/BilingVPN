import os
import sqlite3
import random
import string
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey123'  # Замени на безопасный ключ в продакшене

# HTML-шаблоны как строки
TEMPLATES = {
    'index.html': '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VPN Биллинг</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen flex flex-col">
    <header class="bg-gray-800 p-4">
        <h1 class="text-2xl font-bold">Xray VPN Биллинг</h1>
        <nav class="mt-2">
            <a href="{{ url_for('index') }}" class="text-blue-400 hover:text-blue-300 mr-4">Главная</a>
            {% if 'user_id' in session %}
                <a href="{{ url_for('dashboard') }}" class="text-blue-400 hover:text-blue-300 mr-4">Панель</a>
                {% if session.get('is_admin') %}
                    <a href="{{ url_for('admin_panel') }}" class="text-blue-400 hover:text-blue-300 mr-4">Админ</a>
                {% endif %}
                <a href="{{ url_for('logout') }}" class="text-blue-400 hover:text-blue-300">Выйти</a>
            {% else %}
                <a href="{{ url_for('login') }}" class="text-blue-400 hover:text-blue-300 mr-4">Вход</a>
                <a href="{{ url_for('register') }}" class="text-blue-400 hover:text-blue-300">Регистрация</a>
            {% endif %}
        </nav>
    </header>
    <main class="flex-grow p-4">
        <div class="max-w-2xl mx-auto">
            <h2 class="text-xl font-semibold mb-4">Добро пожаловать в Xray VPN!</h2>
            <p class="mb-4">Подписка на Xray VPN за 75 рублей/месяц. Закажите сейчас и получите доступ к безопасному VPN с кастомным SNI.</p>
            <a href="{{ url_for('register') }}" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded">Начать</a>
        </div>
    </main>
    <footer class="bg-gray-800 p-4 text-center">
        <p>© 2025 Xray VPN. Все права защищены.</p>
    </footer>
</body>
</html>
''',
    'register.html': '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Регистрация</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen flex flex-col">
    <header class="bg-gray-800 p-4">
        <h1 class="text-2xl font-bold">Регистрация</h1>
        <nav class="mt-2">
            <a href="{{ url_for('index') }}" class="text-blue-400 hover:text-blue-300 mr-4">Главная</a>
            <a href="{{ url_for('login') }}" class="text-blue-400 hover:text-blue-300">Вход</a>
        </nav>
    </header>
    <main class="flex-grow p-4">
        <div class="max-w-md mx-auto">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="bg-red-600 p-2 rounded mb-4">
                        {% Cumberland_1st_pos="1">{% for message in messages %}
                            <p>{{ message }}</p>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            <form method="POST" action="{{ url_for('register') }}">
                <div class="mb-4">
                    <label for="username" class="block mb-2">Имя пользователя:</label>
                    <input type="text" id="username" name="username" required class="w-full p-2 bg-gray-800 rounded text-white">
                </div>
                <div class="mb-4">
                    <label for="password" class="block mb-2">Пароль:</label>
                    <input type="password" id="password" name="password" required class="w-full p-2 bg-gray-800 rounded text-white">
                </div>
                <div class="mb-4">
                    <label for="wallet" class="block mb-2">Кошелек (для выплат):</label>
                    <input type="text" id="wallet" name="wallet" required class="w-full p-2 bg-gray-800 rounded text-white">
                </div>
                <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded">Зарегистрироваться</button>
            </form>
        </div>
    </main>
    <footer class="bg-gray-800 p-4 text-center">
        <p>© 2025 Xray VPN. Все права защищены.</p>
    </footer>
</body>
</html>
''',
    'login.html': '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen flex flex-col">
    <header class="bg-gray-800 p-4">
        <h1 class="text-2xl font-bold">Вход</h1>
        <nav class="mt-2">
            <a href="{{ url_for('index') }}" class="text-blue-400 hover:text-blue-300 mr-4">Главная</a>
            <a href="{{ url_for('register') }}" class="text-blue-400 hover:text-blue-300">Регистрация</a>
        </nav>
    </header>
    <main class="flex-grow p-4">
        <div class="max-w-md mx-auto">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="bg-red-600 p-2 rounded mb-4">
                        {% for message in messages %}
                            <p>{{ message }}</p>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            <form method="POST" action="{{ url_for('login') }}">
                <div class="mb-4">
                    <label for="username" class="block mb-2">Имя пользователя:</label>
                    <input type="text" id="username" name="username" required class="w-full p-2 bg-gray-800 rounded text-white">
                </div>
                <div class="mb-4">
                    <label for="password" class="block mb-2">Пароль:</label>
                    <input type="password" id="password" name="password" required class="w-full p-2 bg-gray-800 rounded text-white">
                </div>
                <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded">Войти</button>
            </form>
        </div>
    </main>
    <footer class="bg-gray-800 p-4 text-center">
        <p>© 2025 Xray VPN. Все права защищены.</p>
    </footer>
</body>
</html>
''',
    'dashboard.html': '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Панель пользователя</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen flex flex-col">
    <header class="bg-gray-800 p-4">
        <h1 class="text-2xl font-bold">Панель пользователя</h1>
        <nav class="mt-2">
            <a href="{{ url_for('index') }}" class="text-blue-400 hover:text-blue-300 mr-4">Главная</a>
            <a href="{{ url_for('instructions') }}" class="text-blue-400 hover:text-blue-300 mr-4">Инструкции</a>
            <a href="{{ url_for('logout') }}" class="text-blue-400 hover:text-blue-300">Выйти</a>
        </nav>
    </header>
    <main class="flex-grow p-4">
        <div class="max-w-2xl mx-auto">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="bg-blue-600 p-2 rounded mb-4">
                        {% for message in messages %}
                            <p>{{ message }}</p>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            <h2 class="text-xl font-semibold mb-4">Привет, {{ user[1] }}!</h2>
            <p class="mb-4">Кошелек: {{ user[3] }}</p>
            <form method="POST" action="{{ url_for('create_transaction') }}" class="mb-8">
                <div class="mb-4">
                    <label for="sni" class="block mb-2">Кастомный SNI (опционально):</label>
                    <input type="text" id="sni" name="sni" class="w-full p-2 bg-gray-800 rounded text-white">
                </div>
                <p class="mb-4">Цена: 75 рублей/месяц</p>
                <p class="mb-4 text-sm text-gray-400">После оплаты (до 5 дней) вы получите код транзакции. Укажите его в комментарии к платежу на DonationAlerts.</p>
                <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded">Создать транзакцию</button>
            </form>
            <h3 class="text-lg font-semibold mb-2">Ваши транзакции</h3>
            <ul class="mb-8">
                {% for t in transactions %}
                    <li class="mb-2">Код: {{ t[2] }} | Сумма: {{ t[3] }} руб | Статус: {{ t[4] }} | Создано: {{ t[5] }}</li>
                {% endfor %}
            </ul>
            <h3 class="text-lg font-semibold mb-2">Ваши заказы</h3>
            <ul>
                {% for o in orders %}
                    <li class="mb-2">
                        Заказ #{{ o[0] }} | SNI: {{ o[3] or 'Нет' }} | Ссылка: {{ o[4] or 'Ожидает' }} | 
                        Статус: {{ o[5] }} | Создано: {{ o[6] }}
                    </li>
                {% endfor %}
            </ul>
        </div>
    </main>
    <footer class="bg-gray-800 p-4 text-center">
        <p>© 2025 Xray VPN. Все права защищены.</p>
    </footer>
</body>
</html>
''',
    'admin.html': '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админ-панель</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen flex flex-col">
    <header class="bg-gray-800 p-4">
        <h1 class="text-2xl font-bold">Админ-панель</h1>
        <nav class="mt-2">
            <a href="{{ url_for('index') }}" class="text-blue-400 hover:text-blue-300 mr-4">Главная</a>
            <a href="{{ url_for('logout') }}" class="text-blue-400 hover:text-blue-300">Выйти</a>
        </nav>
    </header>
    <main class="flex-grow p-4">
        <div class="max-w-4xl mx-auto">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="bg-blue-600 p-2 rounded mb-4">
                        {% for message in messages %}
                            <p>{{ message }}</p>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            <h2 class="text-xl font-semibold mb-4">Транзакции</h2>
            <table class="w-full mb-8 bg-gray-800 rounded">
                <thead>
                    <tr>
                        <th class="p-2">ID</th>
                        <th class="p-2">Пользователь</th>
                        <th class="p-2">Код</th>
                        <th class="p-2">Сумма</th>
                        <th class="p-2">Статус</th>
                        <th class="p-2">Действия</th>
                    </tr>
                </thead>
                <tbody>
                    {% for t in transactions %}
                        <tr>
                            <td class="p-2">{{ t[0] }}</td>
                            <td class="p-2">{{ t[5] }}</td>
                            <td class="p-2">{{ t[2] }}</td>
                            <td class="p-2">{{ t[3] }} руб</td>
                            <td class="p-2">{{ t[4] }}</td>
                            <td class="p-2">
                                <form method="POST" action="{{ url_for('update_transaction', transaction_id=t[0]) }}">
                                    <select name="status" class="bg-gray-700 text-white p-1 rounded">
                                        <option value="pending" {% if t[4] == 'pending' %}selected{% endif %}>Ожидает</option>
                                        <option value="completed" {% if t[4] == 'completed' %}selected{% endif %}>Завершено</option>
                                        <option value="failed" {% if t[4] == 'failed' %}selected{% endif %}>Отклонено</option>
                                    </select>
                                    <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white px-2 py-1 rounded">Обновить</button>
                                </form>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
            <h2 class="text-xl font-semibold mb-4">Заказы</h2>
            <table class="w-full bg-gray-800 rounded">
                <thead>
                    <tr>
                        <th class="p-2">ID</th>
                        <th class="p-2">Пользователь</th>
                        <th class="p-2">SNI</th>
                        <th class="p-2">Ссылка VPN</th>
                        <th class="p-2">Статус</th>
                        <th class="p-2">Действия</th>
                    </tr>
                </thead>
                <tbody>
                    {% for o in orders %}
                        <tr>
                            <td class="p-2">{{ o[0] }}</td>
                            <td class="p-2">{{ o[7] }}</td>
                            <td class="p-2">{{ o[3] or 'Нет' }}</td>
                            <td class="p-2">{{ o[4] or 'Ожидает' }}</td>
                            <td class="p-2">{{ o[5] }}</td>
                            <td class="p-2">
                                <form method="POST" action="{{ url_for('update_order', order_id=o[0]) }}">
                                    <input type="text" name="vpn_link" value="{{ o[4] or '' }}" class="bg-gray-700 text-white p-1 rounded mb-2 w-full" placeholder="VPN ссылка">
                                    <select name="status" class="bg-gray-700 text-white p-1 rounded mb-2 w-full">
                                        <option value="pending" {% if o[5] == 'pending' %}selected{% endif %}>Ожидает</option>
                                        <option value="completed" {% if o[5] == 'completed' %}selected{% endif %}>Завершено</option>
                                        <option value="failed" {% if o[5] == 'failed' %}selected{% endif %}>Отклонено</option>
                                    </select>
                                    <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white px-2 py-1 rounded">Обновить</button>
                                </form>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </main>
    <footer class="bg-gray-800 p-4 text-center">
        <p>© 2025 Xray VPN. Все права защищены.</p>
    </footer>
</body>
</html>
''',
    'instructions.html': '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Инструкции по настройке</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen flex flex-col">
    <header class="bg-gray-800 p-4">
        <h1 class="text-2xl font-bold">Инструкции по настройке Xray VPN</h1>
        <nav class="mt-2">
            <a href="{{ url_for('index') }}" class="text-blue-400 hover:text-blue-300 mr-4">Главная</a>
            {% if 'user_id' in session %}
                <a href="{{ url_for('dashboard') }}" class="text-blue-400 hover:text-blue-300 mr-4">Панель</a>
                <a href="{{ url_for('logout') }}" class="text-blue-400 hover:text-blue-300">Выйти</a>
            {% else %}
                <a href="{{ url_for('login') }}" class="text-blue-400 hover:text-blue-300">Вход</a>
            {% endif %}
        </nav>
    </header>
    <main class="flex-grow p-4">
        <div class="max-w-2xl mx-auto">
            <h2 class="text-xl font-semibold mb-4">Как настроить Xray VPN</h2>
            <p class="mb-4">1. После оплаты (до 5 дней) и выполнения заказа (до 3 дней) вы получите ссылку на VPN в панели пользователя.</p>
            <p class="mb-4">2. Скачайте клиент Xray для вашей платформы (Windows, macOS, Linux, Android, iOS).</p>
            <p class="mb-4">3. Импортируйте полученную ссылку в клиент Xray.</p>
            <p class="mb-4">4. Если вы указали кастомный SNI, он будет включен в конфигурацию.</p>
            <p class="mb-4">5. Подключитесь к VPN и наслаждайтесь безопасным интернетом!</p>
            <p class="mb-4">Примечание: Если возникнут проблемы, свяжитесь с поддержкой через DonationAlerts.</p>
        </div>
    </main>
    <footer class="bg-gray-800 p-4 text-center">
        <p>© 2025 Xray VPN. Все права защищены.</p>
    </footer>
</body>
</html>
'''
}

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('billing.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        wallet TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        transaction_code TEXT UNIQUE,
        amount REAL,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        transaction_id INTEGER,
        sni TEXT,
        vpn_link TEXT,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (transaction_id) REFERENCES transactions(id)
    )''')
    # Создаем админа, если его нет
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, wallet) VALUES (?, ?, ?)",
                 ('admin', generate_password_hash('admin123'), 'admin_wallet'))
    conn.commit()
    conn.close()

init_db()

# Генерация случайного кода транзакции
def generate_transaction_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Главная страница
@app.route('/')
def index():
    return render_template_string(TEMPLATES['index.html'])

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        wallet = request.form['wallet']
        conn = sqlite3.connect('billing.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, wallet) VALUES (?, ?, ?)",
                     (username, generate_password_hash(password), wallet))
            conn.commit()
            flash('Регистрация успешна! Войдите в систему.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Имя пользователя уже занято.')
        conn.close()
    return render_template_string(TEMPLATES['register.html'])

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('billing.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = username == 'admin'
            flash('Вход выполнен успешно!')
            return redirect(url_for('dashboard'))
        flash('Неверное имя пользователя или пароль.')
    return render_template_string(TEMPLATES['login.html'])

# Выход
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.')
    return redirect(url_for('index'))

# Панель пользователя
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('billing.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    
    c.execute("SELECT * FROM transactions WHERE user_id = ?", (session['user_id'],))
    transactions = c.fetchall()
    c.execute("SELECT * FROM orders WHERE user_id = ?", (session['user_id'],))
    orders = c.fetchall()
    conn.close()
    
    return render_template_string(TEMPLATES['dashboard.html'], user=user, transactions=transactions, orders=orders)

# Создание транзакции
@app.route('/create_transaction', methods=['POST'])
def create_transaction():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))
    
    sni = request.form.get('sni', '')
    amount = 75.00
    transaction_code = generate_transaction_code()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect('billing.db')
    c = conn.cursor()
    c.execute("INSERT INTO transactions (user_id, transaction_code, amount, status, created_at) VALUES (?, ?, ?, ?, ?)",
             (session['user_id'], transaction_code, amount, 'pending', created_at))
    transaction_id = c.lastrowid
    
    c.execute("INSERT INTO orders (user_id, transaction_id, sni, status, created_at) VALUES (?, ?, ?, ?, ?)",
             (session['user_id'], transaction_id, sni, 'pending', created_at))
    conn.commit()
    conn.close()
    
    flash(f'Транзакция создана! Код: {transaction_code}. Укажите его в комментарии к платежу на DonationAlerts.')
    return redirect(url_for('dashboard'))

# Админ-панель
@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Доступ запрещен.')
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('billing.db')
    c = conn.cursor()
    c.execute("SELECT t.*, u.username FROM transactions t JOIN users u ON t.user_id = u.id")
    transactions = c.fetchall()
    c.execute("SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id")
    orders = c.fetchall()
    conn.close()
    
    return render_template_string(TEMPLATES['admin.html'], transactions=transactions, orders=orders)

# Обновление статуса транзакции
@app.route('/admin/update_transaction/<int:transaction_id>', methods=['POST'])
def update_transaction(transaction_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Доступ запрещен.')
        return redirect(url_for('index'))
    
    status = request.form['status']
    conn = sqlite3.connect('billing.db')
    c = conn.cursor()
    c.execute("UPDATE transactions SET status = ? WHERE id = ?", (status, transaction_id))
    conn.commit()
    conn.close()
    flash('Статус транзакции обновлен.')
    return redirect(url_for('admin_panel'))

# Обновление заказа
@app.route('/admin/update_order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Доступ запрещен.')
        return redirect(url_for('index'))
    
    vpn_link = request.form['vpn_link']
    status = request.form['status']
    conn = sqlite3.connect('billing.db')
    c = conn.cursor()
    c.execute("UPDATE orders SET vpn_link = ?, status = ? WHERE id = ?", (vpn_link, status, order_id))
    conn.commit()
    conn.close()
    flash('Заказ обновлен.')
    return redirect(url_for('admin_panel'))

# Инструкции
@app.route('/instructions')
def instructions():
    return render_template_string(TEMPLATES['instructions.html'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
