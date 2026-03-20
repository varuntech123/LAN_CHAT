"""
Local Network Private Messaging Application
A real-time chat system for LAN communication
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from datetime import datetime
from collections import defaultdict
import socket
import threading
import time

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'lan-chat-secret-key-2024'

# Initialize SocketIO with threading mode for stability
# max_http_buffer_size increased to 50MB for PDF/large file support
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=50 * 1024 * 1024
)

# In-memory storage (no database)
connected_users = {}  # sid -> {username, online, last_seen, color}
private_rooms = defaultdict(list)  # room_id -> [messages]
typing_status = defaultdict(dict)  # room_id -> {username: timestamp}
user_colors = {}  # username -> color

# Predefined user colors for visual distinction
COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
    '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
    '#BB8FCE', '#85C1E9', '#F8B500', '#00CED1'
]

def get_local_ip():
    """Get the local IP address of the host machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_room_id(user1, user2):
    """Generate a consistent room ID for two users (private chat)"""
    sorted_users = sorted([user1.lower(), user2.lower()])
    return f"private_{sorted_users[0]}_{sorted_users[1]}"

def get_user_color(username):
    """Assign a consistent color to each user"""
    if username not in user_colors:
        # Use hash to get consistent color
        color_index = hash(username) % len(COLORS)
        user_colors[username] = COLORS[color_index]
    return user_colors[username]

def broadcast_user_list():
    """Broadcast updated user list to all connected clients"""
    user_list = []
    for sid, user_data in connected_users.items():
        user_list.append({
            'username': user_data['username'],
            'online': user_data['online'],
            'color': user_data.get('color', '#4ECDC4'),
            'last_seen': user_data['last_seen'].isoformat() if user_data.get('last_seen') else None
        })
    socketio.emit('user_list_update', {'users': user_list})


# ==================== Routes ====================

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')


# ==================== Socket Events ====================

@socketio.on('connect')
def handle_connect():
    """Handle new socket connection"""
    print(f"[CONNECT] New connection: {request.sid}")
    emit('connection_established', {
        'sid': request.sid,
        'message': 'Connected to LAN Chat Server'
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnection"""
    if request.sid in connected_users:
        username = connected_users[request.sid]['username']
        print(f"[DISCONNECT] User left: {username}")
        
        # Remove from typing indicators
        for room_id in list(typing_status.keys()):
            if username in typing_status[room_id]:
                del typing_status[room_id][username]
                emit('typing_update', {
                    'username': username,
                    'is_typing': False
                }, room=room_id)
        
        # Remove user
        del connected_users[request.sid]
        broadcast_user_list()


@socketio.on('register_user')
def handle_register_user(data):
    """Register a new user with username"""
    username = data.get('username', '').strip()
    
    if not username:
        emit('registration_failed', {'error': 'Username cannot be empty'})
        return
    
    if len(username) < 2 or len(username) > 20:
        emit('registration_failed', {'error': 'Username must be 2-20 characters'})
        return
    
    # Check if username is already taken
    for sid, user_data in connected_users.items():
        if user_data['username'].lower() == username.lower():
            if sid != request.sid:
                emit('registration_failed', {'error': 'Username already taken'})
                return
    
    # Register the user
    color = get_user_color(username)
    connected_users[request.sid] = {
        'username': username,
        'online': True,
        'color': color,
        'last_seen': datetime.now()
    }
    
    print(f"[REGISTER] User joined: {username}")
    
    emit('registration_success', {
        'username': username,
        'color': color,
        'sid': request.sid
    })
    
    broadcast_user_list()


@socketio.on('open_private_chat')
def handle_open_private_chat(data):
    """Open a private chat room with another user"""
    target_username = data.get('target_username')
    sender_data = connected_users.get(request.sid)
    
    if not sender_data or not target_username:
        emit('error', {'message': 'Invalid chat request'})
        return
    
    sender_username = sender_data['username']
    room_id = get_room_id(sender_username, target_username)
    
    # Join the room
    join_room(room_id)
    
    # Find target user's sid and join them too
    target_sid = None
    for sid, user_data in connected_users.items():
        if user_data['username'].lower() == target_username.lower():
            target_sid = sid
            socketio.server.enter_room(sid, room_id)
            break
    
    emit('private_chat_opened', {
        'room_id': room_id,
        'target_username': target_username,
        'target_online': target_sid is not None
    })
    
    print(f"[CHAT] {sender_username} opened chat with {target_username}")


@socketio.on('send_private_message')
def handle_private_message(data):
    """Handle private message sending"""
    sender_data = connected_users.get(request.sid)
    if not sender_data:
        return
    
    sender_username = sender_data['username']
    sender_color = sender_data['color']
    target_username = data.get('target_username')
    message_content = data.get('message', '').strip()
    
    if not target_username or not message_content:
        return
    
    room_id = get_room_id(sender_username, target_username)
    
    # Create message object
    message_obj = {
        'id': f"msg_{datetime.now().timestamp()}",
        'sender': sender_username,
        'sender_color': sender_color,
        'content': message_content,
        'type': 'text',
        'timestamp': datetime.now().isoformat()
    }
    
    # Store in memory (will be lost on restart)
    private_rooms[room_id].append(message_obj)
    
    # Clear typing indicator for sender
    if sender_username in typing_status.get(room_id, {}):
        del typing_status[room_id][sender_username]
    
    # Emit to room (both sender and receiver)
    emit('receive_private_message', message_obj, room=room_id)
    
    print(f"[MSG] {sender_username} -> {target_username}: {message_content[:30]}...")


@socketio.on('send_file')
def handle_file_send(data):
    """Handle file transfer"""
    sender_data = connected_users.get(request.sid)
    if not sender_data:
        return
    
    sender_username = sender_data['username']
    sender_color = sender_data['color']
    target_username = data.get('target_username')
    file_data = data.get('file')
    filename = data.get('filename', 'unknown_file')
    
    if not target_username or not file_data:
        return
    
    room_id = get_room_id(sender_username, target_username)
    
    # Create file message object
    file_obj = {
        'id': f"file_{datetime.now().timestamp()}",
        'sender': sender_username,
        'sender_color': sender_color,
        'filename': filename,
        'file_data': file_data,
        'type': 'file',
        'timestamp': datetime.now().isoformat()
    }
    
    # Store in memory
    private_rooms[room_id].append(file_obj)
    
    # Emit to room
    emit('receive_file', file_obj, room=room_id)
    
    print(f"[FILE] {sender_username} -> {target_username}: {filename}")


@socketio.on('typing_start')
def handle_typing_start(data):
    """Handle typing indicator start"""
    sender_data = connected_users.get(request.sid)
    if not sender_data:
        return
    
    sender_username = sender_data['username']
    target_username = data.get('target_username')
    
    if not target_username:
        return
    
    room_id = get_room_id(sender_username, target_username)
    typing_status[room_id][sender_username] = datetime.now()
    
    emit('typing_update', {
        'username': sender_username,
        'is_typing': True
    }, room=room_id, include_self=False)


@socketio.on('typing_stop')
def handle_typing_stop(data):
    """Handle typing indicator stop"""
    sender_data = connected_users.get(request.sid)
    if not sender_data:
        return
    
    sender_username = sender_data['username']
    target_username = data.get('target_username')
    
    if not target_username:
        return
    
    room_id = get_room_id(sender_username, target_username)
    
    if room_id in typing_status and sender_username in typing_status[room_id]:
        del typing_status[room_id][sender_username]
    
    emit('typing_update', {
        'username': sender_username,
        'is_typing': False
    }, room=room_id, include_self=False)


@socketio.on('heartbeat')
def handle_heartbeat():
    """Update user's last seen time"""
    if request.sid in connected_users:
        connected_users[request.sid]['last_seen'] = datetime.now()


# ==================== Main Entry ====================

if __name__ == '__main__':
    local_ip = get_local_ip()
    
    print("\n" + "="*60)
    print("        LAN Chat Server - Private Messaging")
    print("="*60)
    print(f"\n  Server running on:")
    print(f"  → Local:   http://localhost:5000")
    print(f"  → Network: http://{local_ip}:5000")
    print("\n  Share the network address with others on your WiFi!")
    print("="*60 + "\n")
    
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=True,
        allow_unsafe_werkzeug=True
    )