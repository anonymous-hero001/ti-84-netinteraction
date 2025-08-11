from flask import Flask, request, jsonify
import uuid
import hashlib
import time
import requests
from datetime import datetime

app = Flask(__name__)

users = {}
sessions = {}
messages = {}
ai_responses = {}

DEEPSEEK_API_KEY = "sk-d27c01d0950743e4b132d338a924b523"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_id():
    return str(uuid.uuid4())

def validate_session(session_id):
    return session_id in sessions and sessions[session_id]['expires'] > time.time()

def query_deepseek_ai(question):
    try:
        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are answering questions. Keep responses short (1-2 sentences), and only use uppercase letters"
                },
                {
                    "role": "user", 
                    "content": question
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_answer = result['choices'][0]['message']['content'].strip()
            return ai_answer.upper()
        else:
            print(f"DeepSeek API error: {response.status_code} - {response.text}")
            return "ERROR: AI SERVICE UNAVAILABLE"
            
    except Exception as e:
        print(f"DeepSeek API exception: {e}")
        return "ERROR: AI REQUEST FAILED"

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if username in users:
        return jsonify({'error': 'Username already exists'}), 400
    
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    
    if len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400
    
    users[username] = {
        'password_hash': hash_password(password),
        'created_at': time.time()
    }
    
    session_id = generate_session_id()
    sessions[session_id] = {
        'username': username,
        'created_at': time.time(),
        'expires': time.time() + 86400
    }
    
    if username not in messages:
        messages[username] = []
    
    if username not in ai_responses:
        ai_responses[username] = []
    
    print(f"✓ New user registered: {username}")
    
    return jsonify({
        'message': 'User created successfully',
        'session_id': session_id,
        'username': username
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if username not in users:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if users[username]['password_hash'] != hash_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    session_id = generate_session_id()
    sessions[session_id] = {
        'username': username,
        'created_at': time.time(),
        'expires': time.time() + 86400
    }
    
    print(f"✓ User logged in: {username}")
    
    return jsonify({
        'message': 'Login successful',
        'session_id': session_id,
        'username': username
    })

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    session_id = data.get('session_id')
    sender = data.get('sender')
    recipient = data.get('recipient')
    message = data.get('message')
    
    if not all([session_id, sender, recipient, message]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if not validate_session(session_id):
        return jsonify({'error': 'Invalid or expired session'}), 401
    
    session_user = sessions[session_id]['username']
    if session_user != sender:
        return jsonify({'error': 'Session user mismatch'}), 401
    
    if recipient not in users:
        return jsonify({'error': 'Recipient not found'}), 404
    
    if recipient not in messages:
        messages[recipient] = []
    
    message_data = {
        'sender': sender,
        'message': message,
        'timestamp': time.time(),
        'formatted_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    messages[recipient].append(message_data)
    
    print(f"✓ Message sent from {sender} to {recipient}: {message}")
    
    return jsonify({
        'message': 'Message sent successfully',
        'timestamp': message_data['formatted_time']
    })

@app.route('/get_messages', methods=['GET'])
def get_messages():
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 400
    
    if not validate_session(session_id):
        return jsonify({'error': 'Invalid or expired session'}), 401
    
    username = sessions[session_id]['username']
    
    if username not in messages:
        messages[username] = []
    
    user_messages = messages[username]
    
    print(f"✓ Retrieved {len(user_messages)} messages for {username}")
    
    return jsonify({
        'messages': user_messages,
        'count': len(user_messages)
    })

@app.route('/ai_question', methods=['POST'])
def ai_question():
    data = request.json
    session_id = data.get('session_id')
    username = data.get('username')
    question = data.get('question')
    
    if not all([session_id, username, question]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if not validate_session(session_id):
        return jsonify({'error': 'Invalid or expired session'}), 401
    
    session_user = sessions[session_id]['username']
    if session_user != username:
        return jsonify({'error': 'Session user mismatch'}), 401
    
    print(f"✓ AI question from {username}: {question}")
    
    ai_answer = query_deepseek_ai(question)
    
    if username not in ai_responses:
        ai_responses[username] = []
    
    response_data = {
        'question': question,
        'answer': ai_answer,
        'timestamp': time.time(),
        'formatted_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    ai_responses[username].append(response_data)
    
    print(f"✓ AI response for {username}: {ai_answer}")
    
    return jsonify({
        'message': 'AI response generated',
        'answer': ai_answer,
        'timestamp': response_data['formatted_time']
    })

@app.route('/get_ai_response', methods=['GET'])
def get_ai_response():
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 400
    
    if not validate_session(session_id):
        return jsonify({'error': 'Invalid or expired session'}), 401
    
    username = sessions[session_id]['username']
    
    if username not in ai_responses:
        ai_responses[username] = []
    
    user_ai_responses = ai_responses[username]
    
    if user_ai_responses:
        latest_response = user_ai_responses[-1]
        print(f"✓ Retrieved AI response for {username}: {latest_response['answer']}")
        
        return jsonify({
            'response': latest_response,
            'answer': latest_response['answer']
        })
    else:
        return jsonify({
            'response': None,
            'answer': ''
        })

@app.route('/status', methods=['GET'])
def status():
    active_sessions = sum(1 for s in sessions.values() if s['expires'] > time.time())
    
    return jsonify({
        'server': 'TI-84 Plus CE Message Server with AI',
        'status': 'running',
        'users': len(users),
        'active_sessions': active_sessions,
        'total_messages': sum(len(msgs) for msgs in messages.values()),
        'total_ai_responses': sum(len(responses) for responses in ai_responses.values()),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/users', methods=['GET'])
def list_users():
    return jsonify({
        'users': list(users.keys()),
        'count': len(users)
    })

def cleanup_expired_sessions():
    current_time = time.time()
    expired_sessions = [sid for sid, session in sessions.items() 
                       if session['expires'] <= current_time]
    
    for sid in expired_sessions:
        username = sessions[sid]['username']
        del sessions[sid]
        print(f"✓ Cleaned up expired session for {username}")

if __name__ == '__main__':
    print("=== TI-84 Plus CE Message Server with AI ===")
    print("Starting server on http://localhost:5000")
    print("="*40)
    
    app.run(host='localhost', port=5000, debug=True)
