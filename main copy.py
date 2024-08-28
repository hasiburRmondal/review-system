from flask import Flask, render_template, request, redirect, url_for, flash, session,Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
from io import StringIO

app = Flask(__name__)

# Set the secret key
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong secret key

# Configure the SQLAlchemy part of the app
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/review_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Dummy login credentials
USERNAME = "admin"
PASSWORD = "admin@123"  # Replace with a strong password

# Review Model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.now)

# Create the database and tables
with app.app_context():
    db.create_all()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))

    reviews = Review.query.all()
    return render_template('dashboard_data.html', reviews=reviews)

@app.route('/review', methods=['GET', 'POST'])
def review():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        rating = request.form['rating']
        comment = request.form['comment']
        
        new_review = Review(name=name, email=email, rating=int(rating), comment=comment)
        db.session.add(new_review)
        db.session.commit()
        flash("Your review was submitted successfully on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "success")
        return redirect(url_for('review'))
    
    return render_template('review_form.html')

@app.route('/export_csv')
def export_csv():
    if not session.get('logged_in'):
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))

    reviews = Review.query.all()
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

if __name__ == '__main__':
    app.run(debug=True)
