from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from flask_migrate import Migrate
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import re  # Import the regular expressions module
from datetime import datetime, timedelta
import csv
from uuid import uuid4
from sqlalchemy import extract
from io import StringIO, BytesIO
import qrcode
import base64
from urllib.parse import quote, unquote

# Import the From external module
from plot_routes import plot_blueprint
from models.ticket import Ticket
from routes.subscriber_compose import subscriber_bp
from routes.admin_view_tickets import admin_bp

app = Flask(__name__)

# Set the secret key
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong secret key

# Configure the SQLAlchemy part of the app
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/review_management'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Welc0me$@localhost/review_management' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Register the blueprint
app.register_blueprint(plot_blueprint)
app.register_blueprint(subscriber_bp)
app.register_blueprint(admin_bp)

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


# Review Model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)  # Add unique=True here
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)

# Create the database and tables - flask migrate is imported 
# with app.app_context():
#     db.create_all()

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

# Function to validate the email format
def is_valid_email(email):
    # Regular expression to validate email format
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)

@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    if request.method == 'POST':

        #Customer Profile
        customer_name = request.form['customer_name']
        customer_phone_number = request.form['customer_phone_number']
        customer_email = request.form['customer_email']
        customer_country = request.form['customer_country']

        # Business Profile
        company_name = request.form['company_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        company_address = request.form['company_address']
        google_review_url = request.form['google_review_url']

        # username/password
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
        user_meta = UserMeta(
            company_name=company_name, 
            email=email, 
            phone_number=phone_number, 
            company_address=company_address, 
            google_review_url=google_review_url,
            customer_name=customer_name,
            customer_phone_number=customer_phone_number,
            customer_email=customer_email,
            customer_country=customer_country,
            user_id=new_user.id
            )
        
        db.session.add(user_meta)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('user_home'))

    return render_template('register.html',user=current_user, user_role=current_user.role)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # if current_user.is_authenticated:
    #     return redirect(url_for('user_home'))
    
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
@app.route('/home', methods=['GET', 'POST'])
@login_required
def user_home():
    user = current_user

    # Check if the user is inactive
    if not user.active:
        flash('This user is inactive.', 'warning')
        return redirect(url_for('login'))

    # Query the total number of users with the role 'subscriber'
    total_users = User.query.filter_by(role='subscriber').count()

    # Query total inactive subscribers
    total_inactive_users = User.query.filter_by(role='subscriber', active=False).count()

    # Query the total number of reviews for the logged-in user
    total_reviews = Review.query.filter_by(user_id=current_user.id).count()

    # Query the total number of All Reviews - Admin Panel
    all_reviews_data = Review.query.count()

    # Calculate last week's start and end dates
    today = datetime.now()
    last_week_start = today - timedelta(days=6)
    last_week_end = today

    # Query to count users registered in the last 7 days
    last_week = datetime.now() - timedelta(days=7)
    total_users_last_week = User.query.filter(User.role == 'subscriber', User.registered_date >= last_week).count()

    # Query to count reviews submitted by the current user in the last 7 days
    total_reviews_last_week = Review.query.filter(
        Review.date_submitted >= last_week_start,
        Review.date_submitted <= last_week_end,
        Review.user_id == current_user.id
    ).count()

    # Fetch distinct years from the reviews for the current user
    years = (
        db.session.query(extract('year', Review.date_submitted))
        .filter(Review.user_id == current_user.id)
        .distinct()
        .all()
    )
    years = [year[0] for year in years]

    # Get the selected year from the form or default to the current year
    selected_year = request.form.get('year', datetime.now().year)

    # Query reviews month-wise for the selected year and current user
    reviews = (
        db.session.query(extract('month', Review.date_submitted), db.func.count(Review.id))
        .filter(extract('year', Review.date_submitted) == int(selected_year))
        .filter(Review.user_id == current_user.id)
        .group_by(extract('month', Review.date_submitted))
        .order_by(extract('month', Review.date_submitted))
        .all()
    )

    # Extract months and counts for plotting
    months = [month for month, count in reviews]
    counts = [count for month, count in reviews]

    # Pass the data to the template
    return render_template(
        'user_home.html',
        total_users=total_users,
        total_users_last_week=total_users_last_week,
        total_inactive_users=total_inactive_users,
        last_week_start=last_week_start.strftime('%Y-%m-%d'),
        last_week_end=last_week_end.strftime('%Y-%m-%d'),
        user=current_user,
        total_reviews=total_reviews,
        total_reviews_last_week=total_reviews_last_week,
        all_reviews_data=all_reviews_data,
        user_role=current_user.role,
        years=years,
        selected_year=selected_year,
        months=months,
        counts=counts
    )


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
    from_date = request.args.get('from_date', '', type=str)
    to_date = request.args.get('to_date', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Base query with user filter
    filters = [Review.user_id == user_id]

    # Add search term filtering if provided
    if search_query:
        filters.append(
            (Review.name.ilike(f'%{search_query}%')) |
            (Review.email.ilike(f'%{search_query}%')) |
            (Review.comment.ilike(f'%{search_query}%'))
        )

    # Handle date filtering
    try:
        if from_date:
            # Convert from_date string to datetime object
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            filters.append(Review.date_submitted >= from_date_obj)
        if to_date:
            # Convert to_date string to datetime object and extend to the end of the day
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            filters.append(Review.date_submitted <= to_date_obj)
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')

    # Apply filters to the query
    reviews = Review.query.filter(*filters).order_by(Review.date_submitted.desc())

    # Paginate the results
    pagination = reviews.paginate(page=page, per_page=per_page, error_out=False)
    reviews = pagination.items

    # Flag to show "No results found" if the reviews list is empty
    no_results = len(reviews) == 0

    return render_template(
        'dashboard_data.html',
        reviews=reviews,
        pagination=pagination,
        search_query=search_query,
        from_date=from_date,
        to_date=to_date,
        user=current_user,
        user_role=current_user.role,
        no_results=no_results
    )

@app.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'administrator':
        flash('Access denied. Administrators only.', 'danger')
        return redirect(url_for('dashboard'))

    # Handle form submission to change user active status
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        toggle_status = request.form.get('toggle_status')
        user = User.query.get(user_id)
        if user:
            user.active = toggle_status != 'deactivate'
            status = 'deactivated' if not user.active else 'activated'
            flash(f'User {user.username} has been {status}.', 'success')
            db.session.commit()
        else:
            flash('User not found.', 'danger')

    # Get filter parameters
    search_query = request.args.get('search', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    from_date_str = request.args.get('from_date', '', type=str)
    to_date_str = request.args.get('to_date', '', type=str)
    active_status = request.args.get('active_status', '', type=str)

    # Initialize filters
    filters = [User.role == 'subscriber']

    # Prepare date filters
    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            if to_date_str:
                try:
                    to_date = datetime.strptime(to_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
                except ValueError:
                    to_date = from_date
            else:
                to_date = from_date
            filters.append(User.registered_date >= from_date)
            filters.append(User.registered_date <= to_date)
        except ValueError:
            flash('Invalid date format.', 'danger')

    # Apply active status filter
    if active_status:
        filters.append(User.active == (active_status == 'active'))

    # Perform a join to access related UserMeta attributes
    query = User.query.join(User.meta).options(joinedload(User.meta))

    # Split search query into individual words and apply filters
    search_terms = search_query.split()
    for term in search_terms:
        term_filter = (
            User.username.ilike(f'%{term}%') |
            UserMeta.company_name.ilike(f'%{term}%') |
            UserMeta.email.ilike(f'%{term}%') |
            UserMeta.company_address.ilike(f'%{term}%')
        )
        filters.append(term_filter)

    # Apply the combined filters to the query and order by registered date descending
    subscribers = query.filter(*filters).order_by(User.registered_date.desc())

    # Paginate the results
    pagination = subscribers.paginate(page=page, per_page=per_page, error_out=False)
    subscribers = pagination.items

    # Flag to show "No results found" if the subscribers list is empty
    no_results = len(subscribers) == 0

    return render_template(
        'admin_dashboard.html', 
        subscribers=subscribers, 
        pagination=pagination, 
        search_query=search_query,
        user=current_user, 
        user_role=current_user.role,
        no_results=no_results,
        from_date=from_date_str,
        to_date=to_date_str,
        active_status=active_status
    )

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
        email = request.form['email']
        phone_number = request.form['phone_number']
        company_address = request.form['company_address']
        google_review_url = request.form['google_review_url']

        # Ensure the UserMeta exists
        user_meta = current_user.meta
        if not user_meta:
            user_meta = UserMeta(company_name='', email='', phone_number='', company_address='', google_review_url='', user_id=current_user.id)
            db.session.add(user_meta)

        user_meta.company_name = company_name
        user_meta.email = email
        user_meta.phone_number = phone_number
        user_meta.company_address = company_address

        if current_user.role == 'administrator':
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
        # Check which form was submitted
        form_type = request.form.get('form_type')

        if form_type == 'update_customer_profile':
            # Handle profile update form submission
            customer_name = request.form['customer_name']
            customer_phone_number = request.form['customer_phone_number']
            customer_email = request.form['customer_email']
            customer_country = request.form['customer_country']

            # Update the user meta fields
            user.meta.customer_name = customer_name
            user.meta.customer_phone_number = customer_phone_number
            user.meta.customer_email = customer_email
            user.meta.customer_country = customer_country

            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('settings'))

        elif form_type == 'change_customer_password':
            # Handle password change form submission
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
    user_meta.email = request.form['email']
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

        # Validate the form inputs individually
        if not name:
            flash('Name is required.', 'danger')
            return redirect(url_for('create_review', user_id=user_id))
        
        if not email:
            flash('Email is required.', 'danger')
            return redirect(url_for('create_review', user_id=user_id))
        
        # Validate email format
        if not is_valid_email(email):
            flash('Invalid email format. Please provide a valid email address.', 'danger')
            return redirect(url_for('create_review', user_id=user_id))
        
        if not rating:
            flash('Rating is required.', 'danger')
            return redirect(url_for('create_review', user_id=user_id))
        
        if not comment:
            flash('Comment is required.', 'danger')
            return redirect(url_for('create_review', user_id=user_id))    

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

# Route for deleting a review by its ID with login requirement
@app.route('/delete_review/<int:review_id>', methods=['POST'])
@login_required  # Ensures the user must be logged in to access this route
def delete_review(review_id):
    # Query to find the review by its ID
    review = Review.query.get(review_id)
    
    # Check if the review exists
    if review:
        try:
            # Delete the review
            db.session.delete(review)
            # Commit the changes to the database
            db.session.commit()
            flash('Review deleted successfully.', 'success')
        except Exception as e:
            # Handle any errors during the deletion process
            db.session.rollback()
            flash(f'Error deleting review: {str(e)}', 'danger')
    else:
        flash('Review not found.', 'warning')
    
    # Redirect back to the dashboard after deletion
    return redirect(url_for('dashboard'))

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

# Export All Reviews - dasboard
@app.route('/export_csv')
@login_required
def export_csv():
    user = current_user
    # Check if the user is inactive
    if not user.active:
        flash('This user is inactive.', 'warning')
        return redirect(url_for('login'))

    # Get date filters from request
    from_date = request.args.get('from_date', '', type=str)
    to_date = request.args.get('to_date', '', type=str)

    # Base query with user filter
    filters = [Review.user_id == user.id]

    # Apply date filtering if provided
    try:
        if from_date:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            filters.append(Review.date_submitted >= from_date_obj)
        if to_date:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            filters.append(Review.date_submitted <= to_date_obj)
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
        return redirect(url_for('dashboard'))

    # Query filtered reviews
    if filters:
        reviews = Review.query.filter(*filters).all()
    else:
        reviews = Review.query.filter_by(user_id=user.id).all()
    
    # Prepare CSV output
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Email', 'Rating', 'Comments', 'Date Submitted'])

    for review in reviews:
        writer.writerow([
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

# Export All User Data - admin/dashboard
@app.route('/admin/dashboard/download_csv', methods=['GET'])
@login_required
def download_csv():
    if current_user.role != 'administrator':
        flash('Access denied. Administrators only.', 'danger')
        return redirect(url_for('dashboard'))

    # Get filter parameters
    search_query = request.args.get('search', '', type=str)
    from_date_str = request.args.get('from_date', '', type=str)
    to_date_str = request.args.get('to_date', '', type=str)
    active_status = request.args.get('active_status', '', type=str)

    # Initialize filters
    filters = [User.role == 'subscriber']

    # Prepare date filters
    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            if to_date_str:
                try:
                    to_date = datetime.strptime(to_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
                except ValueError:
                    to_date = from_date
            else:
                to_date = from_date
            filters.append(User.registered_date >= from_date)
            filters.append(User.registered_date <= to_date)
        except ValueError:
            flash('Invalid date format.', 'danger')

    # Apply active status filter
    if active_status:
        filters.append(User.active == (active_status == 'active'))

    # Perform a join to access related UserMeta attributes
    query = User.query.join(User.meta).options(joinedload(User.meta))

    # Split search query into individual words and apply filters
    search_terms = search_query.split()
    for term in search_terms:
        term_filter = (
            User.username.ilike(f'%{term}%') |
            UserMeta.company_name.ilike(f'%{term}%') |
            UserMeta.email.ilike(f'%{term}%') |
            UserMeta.company_address.ilike(f'%{term}%')
        )
        filters.append(term_filter)

    # Apply the combined filters to the query
    subscribers = query.filter(*filters).all()

    # Create a CSV response using StringIO
    def generate_csv():
        # Use StringIO to create an in-memory file-like object
        output = StringIO()
        writer = csv.writer(output)

        # Write the CSV header
        writer.writerow(['No', 'Username', 'Company Name', 'Email', 'Company Address', 'Registered On', 'Status'])

        # Write the CSV rows
        for index, subscriber in enumerate(subscribers, start=1):
            writer.writerow([
                index,
                subscriber.username,
                subscriber.meta.company_name,
                subscriber.meta.email,
                subscriber.meta.company_address,
                subscriber.registered_date,
                'Active' if subscriber.active else 'Inactive'
            ])

        # Retrieve the CSV content from the StringIO object
        output.seek(0)
        return output.getvalue()

    # Create a response object for the CSV
    response = Response(generate_csv(), mimetype='text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename='all_users.csv')

    return response


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)
