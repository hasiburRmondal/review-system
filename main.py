from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import csv
from uuid import uuid4
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from io import StringIO, BytesIO
import qrcode
import base64
from urllib.parse import quote, unquote

app = Flask(__name__)

# Set the secret key
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong secret key

# Configure the SQLAlchemy part of the app
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/review_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='subscriber')
    active = db.Column(db.Boolean, default=True)
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
    phone_number = db.Column(db.String(15))
    company_address = db.Column(db.String(250))
    google_review_url = db.Column(db.Text)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)

    def __init__(self, company_name, phone_number, company_address, user_id):
        self.company_name = company_name
        self.phone_number = phone_number
        self.company_address = company_address
        self.user_id = user_id

# Review Model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)  # Add unique=True here
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)

# Create the database and tables
with app.app_context():
    db.create_all()

# Define user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.template_filter('urlencode')
def urlencode_filter(value):
    return quote(value)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'administrator':
            flash('Access denied. Administrators only.', 'danger')
            return redirect(url_for('user_home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))

        # Create a new user with hashed password
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Create the UserMeta record for the user
        user_meta = UserMeta(company_name='', phone_number='', company_address='', user_id=new_user.id)
        db.session.add(user_meta)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('user_home'))

    return render_template('register.html',user=current_user, user_role=current_user.role)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user_home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch the user from the database
        user = User.query.filter_by(username=username).first()

        # Check if the user is inactive
        if not user.active:
            flash('This user is inactive.', 'warning')
            return redirect(url_for('login'))
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('user_home'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# Home Page (Index)
@app.route('/')
def index():
    return render_template('index.html')

# User Home
@app.route('/home')
@login_required
def user_home():

    user = current_user
    # Check if the user is inactive
    if not user.active:
        flash('This user is inactive.', 'warning')
        return redirect(url_for('login'))
    
    # Query the total number of users with the role 'subscriber'
    total_users = User.query.filter_by(role='subscriber').count()

    # Query the total number of reviews for the logged-in user
    total_reviews = Review.query.filter_by(user_id=current_user.id).count()

    # Pass the counts to the template
    return render_template('user_home.html', total_users=total_users, user=current_user, total_reviews=total_reviews, user_role=current_user.role)

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():

    user = current_user
    # Check if the user is inactive
    if not user.active:
        flash('This user is inactive.', 'warning')
        return redirect(url_for('login'))

    user_id = current_user.id
    search_query = request.args.get('search', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Modify the query based on the search term
    if search_query:
        reviews = Review.query.filter(
            Review.user_id == user_id,
            (Review.name.ilike(f'%{search_query}%')) |
            (Review.email.ilike(f'%{search_query}%')) |
            (Review.comment.ilike(f'%{search_query}%'))
        )
    else:
        reviews = Review.query.filter_by(user_id=user_id)

    pagination = reviews.paginate(page=page, per_page=per_page, error_out=False)
    reviews = pagination.items

    return render_template('dashboard_data.html', 
                           reviews=reviews, 
                           pagination=pagination, 
                           search_query=search_query,
                           user=current_user, 
                           user_role=current_user.role)

@app.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'administrator':
        flash('Access denied. Administrators only.', 'danger')
        return redirect(url_for('dashboard'))

    # Handle the form submission to change user active status
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        toggle_status = request.form.get('toggle_status')
        user = User.query.get(user_id)
        if user:
            if toggle_status == 'deactivate':
                user.active = False
                flash(f'User {user.username} has been deactivated.', 'success')
            else:
                user.active = True
                flash(f'User {user.username} has been activated.', 'success')
            db.session.commit()
        else:
            flash('User not found.', 'danger')

    # Search functionality
    search_query = request.args.get('search', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Modify the query based on the search term
    if search_query:
        subscribers = User.query.filter(
            User.role == 'subscriber',
            (User.username.ilike(f'%{search_query}%')) |
            (User.meta.has(company_name=search_query)) |
            (User.meta.has(phone_number=search_query)) |
            (User.meta.has(company_address=search_query))
        )
    else:
        subscribers = User.query.filter_by(role='subscriber')

    pagination = subscribers.paginate(page=page, per_page=per_page, error_out=False)
    subscribers = pagination.items

    return render_template('admin_dashboard.html', 
                           subscribers=subscribers, 
                           pagination=pagination, 
                           search_query=search_query,
                           user=current_user, 
                           user_role=current_user.role)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    user = current_user
    # Check if the user is inactive
    if not user.active:
        flash('This user is inactive.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        company_name = request.form['company_name']
        phone_number = request.form['phone_number']
        company_address = request.form['company_address']
        google_review_url = request.form['google_review_url']

        # Ensure the UserMeta exists
        user_meta = current_user.meta
        if not user_meta:
            user_meta = UserMeta(company_name='', phone_number='', company_address='', google_review_url='', user_id=current_user.id)
            db.session.add(user_meta)

        user_meta.company_name = company_name
        user_meta.phone_number = phone_number
        user_meta.company_address = company_address
        user_meta.google_review_url = google_review_url

        db.session.commit()

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))

    return render_template('user_profile.html', user=current_user, user_role=current_user.role)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():

    user = current_user
    # Check if the user is inactive
    if not user.active:
        flash('This user is inactive.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Ensure new password and confirm password match
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('settings'))

        # Update the user's password
        current_user.set_password(new_password)
        db.session.commit()

        flash('Password updated successfully.', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', user=current_user, user_role=current_user.role)

@app.route('/admin/change_password/<user_id>', methods=['POST'])
@login_required
def change_subscriber_password(user_id):
    if current_user.role != 'administrator':
        flash('Access denied. Administrators only.', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('view_subscriber_profile', user_id=user_id))

    user.set_password(new_password)
    db.session.commit()

    flash('Password changed successfully.', 'success')
    return redirect(url_for('view_subscriber_profile', user_id=user_id))


@app.route('/admin/view_subscriber/<user_id>')
@login_required
def view_subscriber_profile(user_id):
    if current_user.role != 'administrator':
        flash('Access denied. Administrators only.', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    
    if user.role != 'subscriber':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('subscriber_profile.html', user=user, user_role=current_user.role, current_user=current_user)

@app.route('/admin/update_subscriber/<user_id>', methods=['POST'])
@login_required
def update_subscriber_profile(user_id):
    if current_user.role != 'administrator':
        flash('Access denied. Administrators only.', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    
    if user.role != 'subscriber':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Update user meta information
    user_meta = user.meta
    user_meta.company_name = request.form['company_name']
    user_meta.phone_number = request.form['phone_number']
    user_meta.company_address = request.form['company_address']
    user_meta.google_review_url = request.form['google_review_url']

    db.session.commit()
    flash('Profile updated successfully.', 'success')

    return redirect(url_for('view_subscriber_profile', user_id=user.id, user_role=current_user.role))


@app.route('/create_review/<user_id>', methods=['GET', 'POST'])
def create_review(user_id):
    user = User.query.get(user_id)

    if not user:
        flash('User not found. Please try again.', 'danger')
        return redirect(url_for('login'))

    # Check if the user is inactive
    if not user.active:
        flash('This user is inactive and cannot submit reviews.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        rating = request.form['rating']
        comment = request.form['comment']

        # Check if a review with the same email already exists
        existing_review = Review.query.filter_by(email=email).first()
        if existing_review:
            flash('A review with this email already exists.', 'danger')
            return redirect(url_for('create_review', user_id=user.id))

        new_review = Review(name=name, email=email, rating=int(rating), comment=comment, user_id=user.id)
        db.session.add(new_review)
        db.session.commit()
        flash("Your review was submitted successfully on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "success")
        return redirect(url_for('create_review', user_id=user.id))

    return render_template('review_form.html', user=user)

@app.route('/review/<encoded_email>')
@login_required
def view_review(encoded_email):

    user = current_user
    # Check if the user is inactive
    if not user.active:
        flash('This user is inactive.', 'warning')
        return redirect(url_for('login'))
    
    email = unquote(encoded_email)
    review = Review.query.filter_by(email=email).first_or_404()
    return render_template('review_detail.html', review=review,
                           user=current_user, 
                           user_role=current_user.role)

@app.route('/generate_qr/<user_id>', methods=['GET','POST'])
@login_required
def generate_qr(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if the user is inactive
    if not user.active:
        flash('This user is inactive and cannot generate a QR code.', 'warning')
        return redirect(url_for('login'))  # or another appropriate page

    # Use url_for to generate the URL
    review_url = url_for('create_review', user_id=user_id, _external=True)

    # Create a QR code object
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(review_url)
    qr.make(fit=True)

    # Generate the image
    img = qr.make_image(fill_color="black", back_color="white")
    byte_io = BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)

    # Convert image to a base64 string
    qr_code_data = base64.b64encode(byte_io.getvalue()).decode('utf-8')
    qr_code_url = f"data:image/png;base64,{qr_code_data}"

    # Render the HTML page with the QR code
    return render_template('qr_code.html', qr_code_url=qr_code_url, user=user, user_role=current_user.role)

@app.route('/export_csv')
@login_required
def export_csv():

    user = current_user
    # Check if the user is inactive
    if not user.active:
        flash('This user is inactive.', 'warning')
        return redirect(url_for('login'))
    
    reviews = Review.query.filter_by(user_id=current_user.id).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Rating', 'Comment', 'Date Submitted'])

    for review in reviews:
        writer.writerow([
            review.id,
            review.name,
            review.email,
            review.rating,
            review.comment,
            review.date_submitted
        ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=reviews.csv"}
    )

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
