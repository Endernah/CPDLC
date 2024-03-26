from flask import Flask, request, jsonify, render_template, redirect, logging
import random, json, bcrypt, json

# AUTHENTICATION

atc_codes = {}
admin_codes = {}
cpdlc_codes = {}
admins = open('admin.json', 'r').read()
admins = json.loads(admins)

def auth_admin(user, passwd):
    if not bcrypt.checkpw(passwd.encode('utf-8'), admins[user].encode('utf-8')):
        return None
    if f"'user': '{user}'" in str(admin_codes):
        for code, data in admin_codes.items():
            if data['user'] == user:
                print(f"New auth on {request.remote_addr} with code {code} (Codes {admin_codes})")
                return code
    else:
        code = generate_code()
        while code in admin_codes:
            code = generate_code()
        admin_codes[code] = {'user': user}
        print(f"New auth on {request.remote_addr} with code {code} (Codes {admin_codes})")
        return code

def generate_code():
    return ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(12))

def new_code(name, discord, type):
    if type == 'atc':
        code = generate_code()
        while code in atc_codes:
            code = generate_code()
        atc_codes[code] = {'name': name, 'discord': discord}
        return code
    elif type == 'cpdlc':
        code = generate_code()
        while code in cpdlc_codes:
            code = generate_code()
        cpdlc_codes[code] = {'name': name, 'discord': discord}
        return code

def get_code(code, type):
    if type == 'atc':
        if code in atc_codes:
            return atc_codes[code]
    if type == 'admin':
        if code in admin_codes:
            return admin_codes[code]
    elif type == 'cpdlc':
        if code in cpdlc_codes:
            return cpdlc_codes[code]

# APP
        
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/atc')
def atc():
    if not request.args.get('code'):
        return render_template('atc_login.html')
    else:
        return render_template('atc.html', name=atc_codes.get(request.args.get('code')))

@app.route('/cpdlc')
def cpdlc():
    return render_template('cpdlc_login.html')

@app.route('/admin')
def admin():
    if request.args.get('code') is None:
        return render_template('admin_login.html')
    else:
        data = get_code(request.args.get('code'), 'admin')
        if data is not None:
            return render_template('admin.html', user=data['user'])
        else:
            return redirect('/admin')

@app.route('/hash/')
def hash():
    return render_template('hash.html')    

# API

@app.route('/api/login/admin', methods=['GET'])
def admin_login():
    user = request.args.get('user')
    passwd = request.args.get('passwd')
    code = auth_admin(user, passwd)
    if code is not None:
        return redirect('/admin?code=' + code)
    else:
        return redirect("/admin")

@app.route('/api/hash', methods=['GET'])
def hash_action():
    passwd = request.args.get('passwd')
    return bcrypt.hashpw(passwd.encode("utf-8"), bcrypt.gensalt())

# RUN

if __name__ == '__main__':
    app.run(debug=False)