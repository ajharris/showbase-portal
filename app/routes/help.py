from flask import Blueprint, render_template, request, jsonify
from ..models import HelpTicket
from .. import db

help_bp = Blueprint('help', __name__, url_prefix='/help')

@help_bp.route('/help')
def help():
    return render_template('help/help.html')

@help_bp.route('/submit-ticket', methods=['POST'])
def submit_ticket():
    data = request.get_json()
    markdown_content = data.get('markdown', '')

    if markdown_content:
        new_ticket = HelpTicket(content=markdown_content)
        db.session.add(new_ticket)
        db.session.commit()
        return jsonify({'status': 'Ticket submitted successfully!'}), 200
    else:
        return jsonify({'status': 'No content provided!'}), 400