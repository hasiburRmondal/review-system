from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.ticket import Ticket

subscriber_view_bp = Blueprint('subscriber_view_tickets', __name__)

# Route for Subscribers to View Their Tickets
@subscriber_view_bp.route('/subscriber/tickets', methods=['GET'])
@login_required
def view_tickets():
    if current_user.role != 'subscriber':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))

    # Query tickets created by the current subscriber
    tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('subscriber_tickets.html', tickets=tickets)
