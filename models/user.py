from models import db  # Importing db from the models package
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from uuid import uuid4

# User Model
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='subscriber')
    active = db.Column(db.Boolean, default=True)
    registered_date = db.Column(db.DateTime, default=datetime.now)
    reviews = db.relationship('Review', backref='user', lazy=True)
    meta = db.relationship("UserMeta", backref="user", uselist=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return self.active

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

# User Meta Model
class UserMeta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150))
    email = db.Column(db.String(255))
    phone_number = db.Column(db.String(15))
    company_address = db.Column(db.String(250))
    google_review_url = db.Column(db.Text)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)

    # New fields
    customer_name = db.Column(db.String(150))
    customer_phone_number = db.Column(db.String(15))
    customer_email = db.Column(db.String(255))
    customer_country = db.Column(db.String(100))

    def __init__(self, company_name, email, phone_number, company_address, google_review_url, user_id,
                 customer_name=None, customer_phone_number=None, customer_email=None, customer_country=None):
        self.company_name = company_name
        self.email = email
        self.phone_number = phone_number
        self.company_address = company_address
        self.google_review_url = google_review_url
        self.user_id = user_id
        self.customer_name = customer_name
        self.customer_phone_number = customer_phone_number
        self.customer_email = customer_email
        self.customer_country = customer_country

