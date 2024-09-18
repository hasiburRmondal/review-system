from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.ticket import Ticket
from models import db  # Importing db from the models package

subscriber_bp = Blueprint('subscriber_compose', __name__)

# Subscriber Compose Mail
@subscriber_bp.route('/compose-mail', methods=['GET', 'POST'])
@login_required
def compose():
    if current_user.role != 'subscriber':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not subject or not message:
            flash('Subject and message are required.', 'danger')
            return url_for('subscriber_compose.compose')

        new_ticket = Ticket(subject=subject, message=message, user_id=current_user.id)
        db.session.add(new_ticket)
        db.session.commit()
        flash('Your message has been sent to the admin.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('subscriber_compose.html')
