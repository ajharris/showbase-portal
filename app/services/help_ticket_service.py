from app.models import HelpTicket, db

def create_help_ticket(worker, subject, content):
    new_ticket = HelpTicket(
        worker_id=worker.id,
        subject=subject,
        content=content
    )
    db.session.add(new_ticket)
    db.session.commit()

from app.models import HelpTicket, db

def create_help_ticket(worker, subject, content):
    new_ticket = HelpTicket(
        worker_id=worker.id,
        subject=subject,
        content=content
    )
    db.session.add(new_ticket)
    db.session.commit()
