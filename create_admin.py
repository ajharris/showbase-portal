from app import create_app, db
from app.models import Worker

app = create_app()
app.app_context().push()

# Replace these with your actual details
first_name = "Andrew"
last_name = "Harris"
email = "andrew.harris.av@gmail.com"
password = "Ernskyk3!"

# Check if the user already exists
existing_worker = Worker.query.filter_by(email=email).first()

if existing_worker:
    print("User already exists.")
else:
    admin_worker = Worker(
        first_name=first_name,
        last_name=last_name,
        email=email,
        is_admin=True,
        active=True
    )
    admin_worker.set_password(password)
    db.session.add(admin_worker)
    db.session.commit()
    print("Admin user created successfully.")
