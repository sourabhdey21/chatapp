from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from flask import session
import re
import base64
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    messages = db.relationship('Message', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room = db.Column(db.String(50), nullable=False)
    file_url = db.Column(db.String(256), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Track online users per room
online_users = {}

# In-memory room list
rooms = {'general'}

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful!')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Could not create user: {str(e)}')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('chat'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/rooms')
@login_required
def get_rooms():
    return jsonify(sorted(list(rooms)))

@app.route('/create_room', methods=['POST'])
@login_required
def create_room():
    room = request.json.get('room')
    if room and room not in rooms:
        rooms.add(room)
        return jsonify({'success': True, 'room': room})
    return jsonify({'success': False, 'error': 'Room already exists or invalid name'})

@app.route('/messages')
@login_required
def get_messages():
    room = request.args.get('room', 'general')
    messages = Message.query.filter_by(room=room).order_by(Message.timestamp.asc()).limit(50).all()
    return jsonify([
        {
            'user': m.author.username,
            'msg': m.content,
            'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'file_url': m.file_url
        } for m in messages
    ])

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files['file']
    room = request.form.get('room', 'general')
    if file:
        filename = f"{current_user.username}_{int(datetime.utcnow().timestamp())}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # Save message with file_url
        msg = Message(content='', user_id=current_user.id, room=room, file_url=f'/uploads/{filename}')
        db.session.add(msg)
        db.session.commit()
        return jsonify({'success': True, 'file_url': f'/uploads/{filename}', 'user': current_user.username, 'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')})
    return jsonify({'success': False}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# WebSocket events
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    username = current_user.username
    rooms.add(room)
    if room not in online_users:
        online_users[room] = set()
    online_users[room].add(username)
    emit('status', {'msg': f'{username} has joined the room.'}, room=room)
    emit('online_users', {'users': list(online_users[room])}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    username = current_user.username
    if room in online_users and username in online_users[room]:
        online_users[room].remove(username)
        emit('status', {'msg': f'{username} has left the room.'}, room=room)
        emit('online_users', {'users': list(online_users[room])}, room=room)

@socketio.on('disconnect')
def on_disconnect():
    # Remove user from all rooms
    username = current_user.username if current_user.is_authenticated else None
    if username:
        for room, users in online_users.items():
            if username in users:
                users.remove(username)
                emit('online_users', {'users': list(users)}, room=room)

@socketio.on('get_online_users')
def handle_get_online_users(data):
    room = data['room']
    users = list(online_users.get(room, []))
    emit('online_users', {'users': users})

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    message = Message(content=msg, user_id=current_user.id, room=room)
    db.session.add(message)
    db.session.commit()

    # Find mentions
    mentions = re.findall(r'@([\w]+)', msg)
    emit('message', {
        'msg': msg,
        'user': current_user.username,
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'mentions': mentions
    }, room=room)
    # Notify mentioned users
    for username in mentions:
        for sid, user in socketio.server.environ.items():
            if user.get('user') == username:
                emit('mention_notification', {
                    'from': current_user.username,
                    'msg': msg
                }, room=sid)

@socketio.on('typing')
def handle_typing(data):
    room = data['room']
    emit('typing', {'user': current_user.username}, room=room, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    room = data['room']
    emit('stop_typing', {'user': current_user.username}, room=room, include_self=False)

@socketio.on('image')
def handle_image(data):
    room = data['room']
    img_data = data['data']
    name = data.get('name', 'image')
    # Optionally, you could save images to disk or DB, but for now just broadcast
    emit('image', {
        'user': current_user.username,
        'data': img_data,
        'name': name,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True) 