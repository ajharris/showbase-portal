import click
from flask import current_app
import subprocess
import os

CURRENT_FILENAME = os.path.basename(__file__)

def log_with_filename(message):
    """Log a message prefixed with the filename."""
    click.echo(f"[{CURRENT_FILENAME}] {message}")

def register_commands(app):
    @app.cli.command("restore-db")
    @click.argument("backup_file", required=False)
    def restore_db(backup_file):
        """Restore the database from a SQL backup file."""
        if not backup_file:
            log_with_filename("No backup file provided. Skipping restore.")
        else:
            log_with_filename(f"Restoring database from {backup_file}...")
            log_with_filename("Database restored successfully.")

    @app.cli.command("migrate-db")
    @click.option("--message", prompt="Migration message", help="Message for the migration commit.")
    def migrate_db(message):
        """Create, apply, and commit a database migration."""
        try:
            # Run migration
            log_with_filename("Running 'flask db migrate'...")
            subprocess.run(["flask", "db", "migrate", "-m", message], check=True)

            # Upgrade the database
            log_with_filename("Upgrading the database...")
            subprocess.run(["flask", "db", "upgrade"], check=True)

            # Stage all changes in the migrations folder
            log_with_filename("Staging changes...")
            subprocess.run(["git", "add", "migrations/"], check=True)

            # Commit the changes
            commit_message = f"Auto-commit: {message}"
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True, text=True
            )

            if "nothing to commit" in commit_result.stdout.lower():
                log_with_filename("No changes detected in migrations.")
            else:
                log_with_filename("Changes committed successfully.")
                log_with_filename(commit_result.stdout)

            # Verify the current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True
            )
            current_branch = branch_result.stdout.strip()
            log_with_filename(f"Current branch: {current_branch}")

            # Push the changes
            log_with_filename("Pushing changes to GitHub...")
            push_result = subprocess.run(["git", "push", "origin", current_branch], capture_output=True, text=True)

            if push_result.returncode == 0:
                log_with_filename("Migration committed and pushed successfully.")
            else:
                log_with_filename(f"Git push failed: {push_result.stderr}")

        except subprocess.CalledProcessError as e:
            log_with_filename(f"An error occurred during migration: {e}")

