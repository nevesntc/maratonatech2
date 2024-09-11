import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

from db_functions import get_user_by_email, register_user, save_quiz_attempt, get_latest_results, update_user_password

app = Flask(__name__)
app.secret_key = '6rJ6O3YhC9bA9F6w9XHt8M0O9D7cT1H2I5eK3sG7d8L9zQ0wP4uR5vT6xY0aB1'
csrf = CSRFProtect(app)

# Configuração do servidor SMTP
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'megahypeb@gmail.com'
SMTP_PASSWORD = 'thmj cvtn voel wvne'

# Função para enviar e-mail usando smtplib
def send_email(to_email, subject, body):
    message = MIMEMultipart()
    message['From'] = SMTP_USER
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, message.as_string())
            print('E-mail enviado com sucesso!')
    except Exception as e:
        print(f'Erro ao enviar o e-mail: {e}')

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.secret_key)
    return serializer.dumps(email, salt='email-confirmation-salt')

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.secret_key)
    try:
        email = serializer.loads(token, salt='email-confirmation-salt', max_age=expiration)
    except Exception as e:
        print(f'Erro ao confirmar o token: {e}')
        return False
    return email

# Rota de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        try:
            # Verificar se o email já está registrado
            existing_user = get_user_by_email(email)
            if existing_user:
                return render_template('index.html', error="Usuário já registrado", register=True)

            # Armazenar a senha com hashing
            hashed_password = generate_password_hash(senha)
            register_user(email, hashed_password)
            confirmation_link = url_for('confirm_email', token=generate_confirmation_token(email), _external=True)
            send_email(email, 'Registro Completo', f'Clique no link para confirmar seu registro: {confirmation_link}')

            session['email'] = email
            return redirect(url_for('quiz'))
        except sqlite3.IntegrityError:
            return render_template('index.html', error="Erro ao registrar usuário", register=True)
        except Exception as e:
            print(f'Erro ao registrar o usuário: {e}')
            return render_template('index.html', error="Erro ao registrar usuário", register=True)

    return render_template('index.html', register=True)

# Rota de login
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        user = get_user_by_email(email)
        if user:
            # Verificar se a senha em texto claro corresponde ao hash armazenado
            if check_password_hash(user['senha'], senha):
                session['user_id'] = user['id']
                session['email'] = email
                return redirect(url_for('quiz'))
            else:
                # Verificar se a senha fornecida é a mesma que a senha em texto claro armazenada
                if user['senha'] == senha:
                    # Atualizar o hash da senha no banco de dados
                    hashed_password = generate_password_hash(senha)
                    update_user_password(email, hashed_password)
                    session['user_id'] = user['id']
                    session['email'] = email
                    return redirect(url_for('quiz'))
                else:
                    return render_template('index.html', error="Credenciais inválidas")

    return render_template('index.html')

# Rota do quiz
@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    username = session.get('email')

    attempts = get_latest_results(user_id)
    return render_template('quiz.html', username=username, attempts=attempts)

# Rota para salvar o quiz
@app.route('/quiz-submit', methods=['POST'])
def quiz_submit():
    score = request.form.get('score')
    user_id = session.get('user_id')

    if user_id and score:
        save_quiz_attempt(user_id, score)

    return redirect(url_for('quiz'))

# Rota para obter os últimos resultados
@app.route('/latest-results')
def latest_results():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    results = get_latest_results(user_id)
    return jsonify([dict(result) for result in results])

# Rota de logoff
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    return redirect(url_for('index'))

@app.route('/save-score', methods=['POST'])
def save_score():
    data = request.get_json()
    score = data.get('score')
    user_id = session.get('user_id')

    if user_id and score is not None:
        save_quiz_attempt(user_id, score)
        return jsonify({'success': True}), 200
    return jsonify({'success': False, 'message': 'Usuário não autenticado ou pontuação inválida'}), 400

@app.route('/get-results')
def get_results():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    results = get_latest_results(user_id)
    return jsonify([dict(result) for result in results])

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    user = get_user_by_email(email)

    if user:
        senha = user['senha']  # Senha em texto claro
        send_email(email, 'Recuperação de Senha', f'Sua senha é: {senha}')
        return redirect(url_for('index', message='Sua senha foi enviada para seu e-mail.'))
    else:
        return redirect(url_for('index', error='Email não encontrado.'))

if __name__ == '__main__':
    app.run(debug=True)
