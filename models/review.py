# /models/review.py
from models import db  # Importing db from the models package
from datetime import datetime

# Review Model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)  # Add unique=True here
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
