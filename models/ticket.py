# /models/ticket.py
from uuid import uuid4
from datetime import datetime
from models import db

class Ticket(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    reply = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='open')
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)

    def __init__(self, subject, message, user_id):
        self.subject = subject
        self.message = message
        self.user_id = user_id
