from flask import Flask, request, jsonify, render_template, redirect, make_response
import random, json, bcrypt

# AUTHENTICATION

atc_codes = {}
admin_codes = {}
pilot_codes = {}
admins = json.loads(open('admin.json', 'r').read())

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

def new_code(name, discord, type):
    if type == 'atc':
        code = generate_code()
        while code in atc_codes:
            code = generate_code()
        atc_codes[code] = {'name': name, 'discord': discord}
        return code
    elif type == 'pilot':
        code = generate_code()
        while code in pilot_codes:
            code = generate_code()
        pilot_codes[code] = {'name': name, 'discord': discord}
        return code

# APP
        
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/atc')
def atc():
    if not request.cookies.get('code_atc'):
        return render_template('atc_login.html')
    else:
        return render_template('atc.html', name=atc_codes.get(request.cookies.get('code_atc')))

@app.route('/pilot')
def pilot():
    return render_template('pilot_login.html')

@app.route('/admin')
def admin():
    if request.cookies.get('code') is None:
        return render_template('admin_login.html')
    else:
        data = admin_codes.get(request.cookies.get('code'))
        if data is not None:
            return render_template('admin.html', user=data['user'])
        else:
            resp = make_response(redirect('/admin'))
            resp.delete_cookie('code')
            return resp

@app.route('/hasher')
def hash():
    return render_template('hash.html')    

# API

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
    app.run(debug=False)