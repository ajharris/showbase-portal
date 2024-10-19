from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user, login_required
from ..models import HelpTicket
from .. import db

help_bp = Blueprint('help', __name__, url_prefix='/help')

@help_bp.route('/')
def help():
    """Render the help page."""
    return render_template('help/help.html')

import logging

logger = logging.getLogger(__name__)

@help_bp.route('/submit-ticket', methods=['POST'])
@login_required
def submit_ticket():
    data = request.get_json()
    subject = data.get('subject', '')
    markdown_content = data.get('markdown', '')

    if not subject or not markdown_content:
        return jsonify({'status': 'Subject and content are required!'}), 400

    new_ticket = HelpTicket(
        content=markdown_content,
        subject=subject,
        worker_id=current_user.id
    )

    try:
        db.session.add(new_ticket)
        db.session.commit()
        return jsonify({'status': 'Ticket submitted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting ticket: {str(e)}")
        return jsonify({'status': 'Error submitting ticket', 'error': str(e)}), 500
