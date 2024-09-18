from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.ticket import Ticket
from models import db

admin_bp = Blueprint('admin_view_tickets', __name__)

# Admin View Tickets
@admin_bp.route('/admin/tickets', methods=['GET'])
@login_required
def view_tickets():
    if current_user.role != 'administrator':
        flash('Access denied', 'danger')
        return redirect(url_for('user_home'))

    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('admin_tickets.html', tickets=tickets, user_role=current_user.role,)

# Admin View and Reply to a Ticket
@admin_bp.route('/admin/ticket/<ticket_id>', methods=['GET', 'POST'])
@login_required
def view_ticket(ticket_id):
    if current_user.role != 'administrator':
        flash('Access denied', 'danger')
        return redirect(url_for('user_home'))

    ticket = Ticket.query.get_or_404(ticket_id)

    if request.method == 'POST':
        reply = request.form.get('reply')
        status = request.form.get('status')
        ticket.reply = reply
        ticket.status = status
        db.session.commit()
        flash('Ticket updated successfully.', 'success')
        # Include the ticket_id in the redirect to view_ticket
        return redirect(url_for('admin_view_tickets.view_ticket', ticket_id=ticket_id))

    return render_template('view_ticket.html', ticket=ticket, user_role=current_user.role,)
