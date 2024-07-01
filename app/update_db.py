import click
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import text
from app import db  # Adjust the import based on your actual application structure

@click.command("update-db")
@click.argument('backup_file')
@with_appcontext
def update_database_from_backup(backup_file):
    """Update the database from a SQL backup file."""
    non_executable_statements = {'BEGIN TRANSACTION', 'COMMIT', 'ROLLBACK'}
    
    try:
        with open(backup_file, 'r') as file:
            sql_commands = file.read().split(';')
            with db.engine.connect() as connection:
                transaction = connection.begin()
                try:
                    for command in sql_commands:
                        command = command.strip()
                        if command and not any(command.startswith(stmt) for stmt in non_executable_statements):
                            try:
                                connection.execute(text(command))
                            except IntegrityError as e:
                                click.echo(f"Skipping duplicate record: {e}")
                    transaction.commit()
                    click.echo("Database updated successfully from backup.")
                except SQLAlchemyError as e:
                    transaction.rollback()
                    click.echo(f"An error occurred while updating the database: {e}")
    except Exception as e:
        click.echo(f"An error occurred while reading the backup file: {e}")

def register_commands(app):
    app.cli.add_command(update_database_from_backup)
