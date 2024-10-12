from flask import Blueprint, jsonify, request, render_template
from app.models import HelpPost, db

help_bp = Blueprint('help', __name__)

@help_bp.route('/api/posts', methods=['POST'])
def create_post():
    data = request.json
    try:
        new_post = HelpPost(content=data['content'])
        db.session.add(new_post)
        db.session.commit()
        return jsonify({'id': new_post.id}), 201
    except Exception as e:
        db.session.rollback()  # Rollback the session on error
        return jsonify({'error': str(e)}), 400  # Return an error response


@help_bp.route('/api/posts', methods=['GET'])
def get_posts():
    posts = HelpPost.query.all()
    return jsonify([{'id': post.id, 'content': post.content} for post in posts])

@help_bp.route('/help')
def help():
    return render_template('help/help.html')
