import click
from flask import current_app

def register_commands(app):
    @app.cli.command("update-db")
    @click.argument("backup_file", required=False)  # Make it optional
    def update_db(backup_file):
        """Update the database from a SQL backup file."""
        if not backup_file:
            click.echo("No backup file provided. Skipping restore.")
        else:
            click.echo(f"Restoring database from {backup_file}...")
            # Add logic to restore from backup file here

    @app.cli.command("db-update")
    @click.option("--message", prompt="Migration message", help="Message for the migration commit.")
    def db_update(message):
        """Migrate, upgrade, and commit migrations."""
        import subprocess

        click.echo("Running flask db migrate...")
        subprocess.run(["flask", "db", "migrate", "-m", message], check=True)

        click.echo("Upgrading the database...")
        subprocess.run(["flask", "db", "upgrade"], check=True)

        result = subprocess.run(
            ["git", "status", "--porcelain", "migrations/"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            click.echo("Changes detected. Committing to Git...")
            subprocess.run(["git", "add", "migrations/"], check=True)
            commit_message = f"Auto-commit: {message}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
        else:
            click.echo("No changes to commit.")
