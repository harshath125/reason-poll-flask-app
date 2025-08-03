from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# --- NEW USER MODEL ---
class User(UserMixin, db.Model):
    """Represents a user in the database."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user') # Roles: 'user', 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Poll(db.Model):
    """Represents a poll in the database."""
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(300), nullable=False)
    options = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # --- ADDED: Link to the user who created the poll ---
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref=db.backref('polls', lazy=True))
    
    responses = db.relationship('Response', backref='poll', lazy=True, cascade="all, delete-orphan")

    def get_options_list(self):
        return [opt.strip() for opt in self.options.split(',')]

class Response(db.Model):
    """Represents a user's response to a poll."""
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    # --- ADDED: Link to the user who voted ---
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('responses', lazy=True))

    selected_option = db.Column(db.String(100), nullable=False)
    reason_text = db.Column(db.Text, nullable=True)
    sentiment = db.Column(db.String(10), nullable=True)
    keywords = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
