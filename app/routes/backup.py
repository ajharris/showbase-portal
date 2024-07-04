from flask import Blueprint, current_app
from flask_login import login_required
from app.utils import backup_database_to_json, restore_database_from_json

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/backup', methods=['GET'])
@login_required
def backup():
    file_path = 'backup.json'  # Define the path where you want to save the backup
    success = backup_database_to_json(file_path)
    if success:
        return "Backup successful!"
    else:
        return "Backup failed!", 500

@backup_bp.route('/restore', methods=['POST'])
@login_required
def restore():
    file_path = 'backup.json'  # Define the path where you want to restore from
    success = restore_database_from_json(file_path)
    if success:
        return "Restore successful!"
    else:
        return "Restore failed!", 500
