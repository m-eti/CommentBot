import json
import os
import atexit
from collections import deque
from flask import Flask, request, render_template, redirect, url_for, session, flash
from bot import (
    LOG_FILE,
    send_code_request, add_account, start_commenting,
    stop_client, stop_all_clients,
    start_event_loop, stop_event_loop, run_coroutine
)


CONFIG_FILE = "config.json"

app = Flask(__name__)
app.secret_key = os.urandom(24)


def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}

    defaults = {
        "PASSWORD": "admin",
        "API_ID": "",
        "API_HASH": "",
        "accounts": {},
        "comments": [],
    }

    needs_save = not os.path.exists(CONFIG_FILE)
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
            needs_save = True

    if not isinstance(config.get("accounts"), dict):
        config["accounts"] = {}
        needs_save = True

    if needs_save:
        save_config(config)
    return config


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


def read_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return list(deque(f, maxlen=100))
    except FileNotFoundError:
        return []


@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'logged_in' not in session:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        config = load_config()
        password = request.form.get('password')
        if password == config.get('PASSWORD'):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/')
def index():
    config = load_config()
    logs = read_logs()
    from bot import is_running
    return render_template(
        'index.html',
        accounts=config["accounts"],
        comments=config["comments"],
        logs=logs, is_running=is_running
    )


@app.route('/send_code_request', methods=['POST'])
def send_code_request_route():
    phone = request.form['phone']
    config = load_config()

    if phone in config["accounts"] and config["accounts"][phone].get("signed_in"):
        return "This phone number has already been added."

    try:
        phone_code_hash = run_coroutine(send_code_request(phone, config["API_ID"], config["API_HASH"]))
        if phone not in config["accounts"]:
            config["accounts"][phone] = {}
        config["accounts"][phone]["phone_code_hash"] = phone_code_hash
        save_config(config)
    except Exception as e:
        return "An error occurred: " + str(e)
    return redirect(url_for('index'))


@app.route('/add_account', methods=['POST'])
def add_account_route():
    phone = request.form['phone']
    code = request.form['code']
    password = request.form.get('password', None)
    config = load_config()
    if phone in config["accounts"] and config["accounts"][phone].get("signed_in"):
        return "This phone number has already been added."

    phone_code_hash = config.get("accounts", {}).get(phone, {}).get("phone_code_hash")
    if not phone_code_hash:
        return "Please request a code first."

    try:
        result = run_coroutine(add_account(phone, code, phone_code_hash, config["API_ID"], config["API_HASH"], password))
        if result:
            config["accounts"][phone]["signed_in"] = True
            config["accounts"][phone].pop("phone_code_hash", None)
            save_config(config)
    except Exception as e:
        return "An error occurred: " + str(e)
    
    return redirect(url_for('index'))


@app.route('/delete_account', methods=['POST'])
def delete_account():
    phone = request.form['phone']
    
    run_coroutine(stop_client(phone))
    session_file = f'sessions/{phone}.session'
    if os.path.exists(session_file):
        os.remove(session_file)
    config = load_config()
    if phone in config["accounts"]:
        config["accounts"].pop(phone)
        save_config(config)
    return redirect(url_for('index'))


@app.route('/add_comment', methods=['POST'])
def add_comment():
    comment = request.form['comment']
    config = load_config()
    config["comments"].append(comment)
    save_config(config)
    return redirect(url_for('index'))


@app.route('/delete_comment', methods=['POST'])
def delete_comment():
    comment = request.form['comment']

    config = load_config()
    if comment in config["comments"]:
        config["comments"].remove(comment)
        save_config(config)
    return redirect(url_for('index'))


@app.route('/start', methods=['POST'])
def start():
    from bot import is_running
    if not is_running:
        config = load_config()
        if not config["accounts"] or not config["comments"]:
            return "Not enough accounts or comments!"
        
        phones = [phone for phone, info in config["accounts"].items() if info.get("signed_in")]
        if not phones:
            return "No signed-in accounts available to start."
        comments = config["comments"]
        run_coroutine(start_commenting(phones, comments, config["API_ID"], config["API_HASH"]))
    return redirect(url_for('index'))


@app.route('/stop', methods=['POST'])
def stop():
    run_coroutine(stop_all_clients())
    return redirect(url_for('index'))


if __name__ == "__main__":
    os.makedirs('sessions', exist_ok=True)
    start_event_loop()
    atexit.register(stop_event_loop)
    app.run(debug=True)
