from flask import Flask, request, jsonify
import uuid
import hashlib
import time
from datetime import datetime

app = Flask(__name__)

users = {}
sessions = {}
messages = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_id():
    return str(uuid.uuid4())

def validate_session(session_id):
    return session_id in sessions and sessions[session_id]['expires'] > time.time()

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

@app.route('/status', methods=['GET'])
def status():
    active_sessions = sum(1 for s in sessions.values() if s['expires'] > time.time())
    
    return jsonify({
        'server': 'TI-84 Plus CE Message Server',
        'status': 'running',
        'users': len(users),
        'active_sessions': active_sessions,
        'total_messages': sum(len(msgs) for msgs in messages.values()),
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
    print("=== TI-84 Plus CE Message Server ===")
    print("Starting server on http://localhost:5000")
    print("="*40)
    
    app.run(host='0.0.0.0', port=5000, debug=True)