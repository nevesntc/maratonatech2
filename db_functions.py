import sqlite3

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Função para salvar tentativa de quiz
def save_quiz_attempt(user_id, score):
    conn = get_db_connection()
    conn.execute('INSERT INTO quiz_attempts (user_id, score, date) VALUES (?, ?, CURRENT_TIMESTAMP)', (user_id, score))
    conn.commit()
    conn.close()

# Função para obter os últimos resultados do banco de dados
def get_latest_results(user_id):
    conn = get_db_connection()
    results = conn.execute('''
        SELECT score, date FROM quiz_attempts WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 5
    ''', (user_id,)).fetchall()
    conn.close()
    return results

# Função para buscar usuário por email
def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

# Função para registrar um novo usuário
def register_user(email, hashed_password):
    conn = get_db_connection()
    conn.execute('INSERT INTO users (email, senha) VALUES (?, ?)', (email, hashed_password))
    conn.commit()
    user_id = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()['id']
    conn.close()
    return user_id
import sqlite3

def update_user_password(email, hashed_password):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET senha = ? WHERE email = ?', (hashed_password, email))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f'Error updating password: {e}')
