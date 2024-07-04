from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.utils import backup_database_to_json, restore_database_from_json
import os
from datetime import datetime

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/admin/backup_restore')
@login_required
def show_backup_restore():
    return render_template('admin/backup_restore.html')

@backup_bp.route('/admin/backup', methods=['POST'])
@login_required
def backup():
    file_path = request.form.get('backup_path')
    if not file_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join('uploads', 'backups', f'backup_{timestamp}.json')

    success = backup_database_to_json(file_path)
    if success:
        flash(f'Backup successful! File saved to {file_path}', 'success')
    else:
        flash('Backup failed!', 'danger')
    return redirect(url_for('backup.show_backup_restore'))

@backup_bp.route('/admin/restore', methods=['POST'])
@login_required
def restore():
    file_path = request.form.get('restore_path')
    if not file_path:
        # Choose the most recent backup file by default
        backup_dir = os.path.join('uploads', 'backups')
        backup_files = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.json')], key=os.path.getmtime, reverse=True)
        if backup_files:
            file_path = backup_files[0]
        else:
            flash('No backup files found!', 'danger')
            return redirect(url_for('backup.show_backup_restore'))

    success = restore_database_from_json(file_path)
    if success:
        flash(f'Restore successful! Database restored from {file_path}', 'success')
    else:
        flash('Restore failed!', 'danger')
    return redirect(url_for('backup.show_backup_restore'))
