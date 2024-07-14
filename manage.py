from flask.cli import FlaskGroup
from app import create_app, db

app = create_app()
cli = FlaskGroup(app)

if __name__ == "__main__":
    cli()
