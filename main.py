from flask import Flask, request, jsonify, render_template, redirect, make_response
from flask_socketio import SocketIO
import random, json, bcrypt, threading, time

# AUTHENTICATION

atc_codes = {}
admin_codes = {}
pilot_codes = {}
admins = json.loads(open('admin.json', 'r').read())

def active_users():
    return len(atc_codes) + len(pilot_codes)

def auth_admin(user, passwd):
    if not bcrypt.checkpw(passwd.encode('utf-8'), admins[user].encode('utf-8')):
        return None
    if f"'user': '{user}'" in str(admin_codes):
        for code, data in admin_codes.items():
            if data['user'] == user:
                print(f"New auth on {request.remote_addr} with code ...{str(code)[-2:]}")
                return code
    else:
        code = generate_code()
        while code in admin_codes:
            code = generate_code()
        admin_codes[code] = {'user': user}
        print(f"New auth on {request.remote_addr} with code ...{str(code)[-2:]}")
        return code

def generate_code():
    return ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(12))

def new_code(callsign, discord, type):
    if type == 'atc':
        code = generate_code()
        while code in atc_codes:
            code = generate_code()
        atc_codes[code] = {'callsign': callsign, 'discord': discord, 'last_check': time.time()}
        return code
    elif type == 'pilot':
        code = generate_code()
        while code in pilot_codes:
            code = generate_code()
        pilot_codes[code] = {'callsign': callsign, 'discord': discord, 'last_check': time.time()}
        return code

# APP
        
app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/atc')
def atc():
    if not request.cookies.get('code_atc'):
        return render_template('atc_login.html')
    else:
        try:
            callsign = atc_codes.get(request.cookies.get('code_atc'))['callsign']
            discord = atc_codes.get(request.cookies.get('code_atc'))['discord']
            return render_template('atc.html', callsign=callsign, discord=discord, code=request.cookies.get('code_atc'))
        except:
            try: atc_codes.pop(request.cookies.get('code_atc'))
            except: pass
            resp = make_response(redirect('/atc'))
            resp.delete_cookie('code_atc')
            return resp

@app.route('/pilot')
def pilot():
    if not request.cookies.get('code_pilot'):
        return render_template('pilot_login.html')
    else:
        try:
            callsign = pilot_codes.get(request.cookies.get('code_pilot'))['callsign']
            discord = pilot_codes.get(request.cookies.get('code_pilot'))['discord']
            return render_template('pilot.html', callsign=callsign, discord=discord, code=request.cookies.get('code_pilot'))
        except:
            try: pilot_codes.pop(request.cookies.get('code_pilot'))
            except: pass
            resp = make_response(redirect('/pilot'))
            resp.delete_cookie('code_pilot')
            return resp

@app.route('/admin')
def admin():
    if request.cookies.get('code') is None:
        return render_template('admin_login.html')
    else:
        data = admin_codes.get(request.cookies.get('code'))
        if data is not None:
            return render_template('admin.html', user=data['user'], active_users=active_users())
        else:
            resp = make_response(redirect('/admin'))
            resp.delete_cookie('code')
            return resp

@app.route('/hasher')
def hash():
    return render_template('hash.html')    

# SOCKET.IO API

@socketio.on('pilot/connect')
def pilot_connect(code):
    print(f"...{str(code)[-2:]} Pilot connected.")

@socketio.on('atc/connect')
def atc_connect(code):
    print(f"...{str(code)[-2:]} Atc connected.")

@socketio.on('check')
def handle_check(code):
    if code in atc_codes:
        atc_codes[code]['last_check'] = time.time()
    elif code in pilot_codes:
        pilot_codes[code]['last_check'] = time.time()

def check_inactivity():
    while True:
        current_time = time.time()
        inactive_codes = [code for code, data in atc_codes.items() if current_time - data['last_check'] > 5]
        for code in inactive_codes:
            atc_codes.pop(code)
            print(f"...{str(code)[-2:]} Atc disconnected due to inactivity.")
        inactive_codes = [code for code, data in pilot_codes.items() if current_time - data['last_check'] > 5]
        for code in inactive_codes:
            pilot_codes.pop(code)
            print(f"...{str(code)[-2:]} Pilot disconnected due to inactivity.")
        time.sleep(5)

# API

@app.route('/api/login/atc', methods=['GET','POST'])
def atc_login():
    callsign = request.form.get('callsign')
    discord = request.form.get('discord')
    if callsign in [data['callsign'] for data in atc_codes.values()]:
        return "Callsign already taken", 400
    code = new_code(callsign, discord, 'atc')
    resp = make_response(redirect('/atc'))
    resp.set_cookie('code_atc', code)
    return resp

@app.route('/api/login/pilot', methods=['GET','POST'])
def pilot_login():
    callsign = request.form.get('callsign')
    discord = request.form.get('discord')
    if callsign in [data['callsign'] for data in pilot_codes.values()]:
        return "Callsign already taken", 400
    code = new_code(callsign, discord, 'pilot')
    resp = make_response(redirect('/pilot'))
    resp.set_cookie('code_pilot', code)
    return resp

@app.route('/api/login/admin', methods=['GET','POST'])
def admin_login():
    user = request.form.get('user')
    passwd = request.form.get('passwd')
    try:
        code = auth_admin(user, passwd)
    except:
        resp = make_response(redirect('/admin'))
        resp.delete_cookie('code')
        return resp
    if code is not None:
        resp = make_response(redirect('/admin'))
        resp.set_cookie('code', code)
        return resp
    else:
        resp = make_response(redirect('/admin'))
        resp.delete_cookie('code')
        return resp

@app.route('/api/hash', methods=['GET','POST'])
def hash_action():
    try:
        passwd = request.form.get('passwd')
        return bcrypt.hashpw(passwd.encode("utf-8"), bcrypt.gensalt())
    except:
        return "Error accured.", 401

# RUN

if __name__ == '__main__':
    inactivity_thread = threading.Thread(target=check_inactivity)
    inactivity_thread.start()
    socketio.run(app)