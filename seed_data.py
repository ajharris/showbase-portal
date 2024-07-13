import json
from faker import Faker
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

fake = Faker()

def generate_unique_id(existing_ids):
    new_id = fake.random_int(min=1, max=1000)
    while new_id in existing_ids:
        new_id = fake.random_int(min=1, max=1000)
    existing_ids.add(new_id)
    return new_id

def generate_workers(num=10):
    workers = []
    existing_ids = set()
    for _ in range(num):
        worker_id = generate_unique_id(existing_ids)
        worker = {
            "id": worker_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone_number": fake.phone_number(),
            "is_admin": fake.boolean(chance_of_getting_true=10),
            "is_account_manager": fake.boolean(chance_of_getting_true=20),
            "password_hash": generate_password_hash(fake.password()),
            "theme": 'light',
            "active": True,
            "password_is_temp": True
        }
        workers.append(worker)
    return workers

def generate_locations(num=5):
    locations = []
    existing_ids = set()
    for _ in range(num):
        location_id = generate_unique_id(existing_ids)
        location = {
            "id": location_id,
            "name": fake.company(),
            "address": fake.address(),
            "loading_notes": fake.text(max_nb_chars=1024),
            "dress_code": fake.text(max_nb_chars=256),
            "other_info": fake.text(max_nb_chars=1024)
        }
        locations.append(location)
    return locations

def generate_events(num=10, workers=None, locations=None):
    events = []
    existing_ids = set()
    if not workers:
        workers = generate_workers()
    if not locations:
        locations = generate_locations()
    account_manager_ids = [worker["id"] for worker in workers if worker["is_account_manager"]]
    for _ in range(num):
        event_id = generate_unique_id(existing_ids)
        event = {
            "id": event_id,
            "show_name": fake.catch_phrase(),
            "show_number": generate_unique_id(existing_ids),
            "account_manager_id": fake.random_element(elements=account_manager_ids),
            "location_id": fake.random_element(elements=[location["id"] for location in locations]),
            "sharepoint": fake.url(),
            "active": True
        }
        events.append(event)
    return events

def generate_crew(num=10, events=None):
    crews = []
    existing_ids = set()
    if not events:
        events = generate_events()
    for _ in range(num):
        crew_id = generate_unique_id(existing_ids)
        crew = {
            "id": crew_id,
            "event_id": fake.random_element(elements=[event["id"] for event in events]),
            "start_time": fake.date_time_this_year().isoformat(),
            "end_time": (fake.date_time_this_year() + timedelta(hours=4)).isoformat(),
            "roles": json.dumps({"role1": fake.random_int(min=1, max=5)}),
            "shift_type": fake.word(),
            "description": fake.text()
        }
        crews.append(crew)
    return crews

def generate_expenses(num=10, workers=None, events=None):
    expenses = []
    existing_ids = set()
    if not workers:
        workers = generate_workers()
    if not events:
        events = generate_events()
    for _ in range(num):
        expense_id = generate_unique_id(existing_ids)
        expense = {
            "id": expense_id,
            "receipt_number": fake.bothify(text='????-########'),
            "date": fake.date_this_year().isoformat(),
            "account_manager_id": fake.random_element(elements=[worker["id"] for worker in workers]),
            "show_name": fake.catch_phrase(),
            "show_number": fake.random_element(elements=[event["show_number"] for event in events]),
            "details": fake.text(),
            "net": fake.random_number(digits=5),
            "hst": fake.random_number(digits=2),
            "receipt_filename": fake.file_name(extension='pdf'),
            "worker_id": fake.random_element(elements=[worker["id"] for worker in workers])
        }
        expenses.append(expense)
    return expenses

def generate_shifts(num=10, workers=None, events=None):
    shifts = []
    existing_ids = set()
    if not workers:
        workers = generate_workers()
    if not events:
        events = generate_events()
    for _ in range(num):
        shift_id = generate_unique_id(existing_ids)
        shift = {
            "id": shift_id,
            "start": fake.date_time_this_year().isoformat(),
            "end": (fake.date_time_this_year() + timedelta(hours=4)).isoformat(),
            "show_name": fake.catch_phrase(),
            "show_number": fake.random_element(elements=[event["show_number"] for event in events]),
            "account_manager_id": fake.random_element(elements=[worker["id"] for worker in workers]),
            "location": fake.address(),
            "worker_id": fake.random_element(elements=[worker["id"] for worker in workers]),
            "crew_assignment_id": generate_unique_id(existing_ids)
        }
        shifts.append(shift)
    return shifts

def generate_notes(num=10, workers=None, events=None):
    notes = []
    existing_ids = set()
    if not workers:
        workers = generate_workers()
    if not events:
        events = generate_events()
    for _ in range(num):
        note_id = generate_unique_id(existing_ids)
        note = {
            "id": note_id,
            "content": fake.text(),
            "created_at": fake.date_time_this_year().isoformat(),
            "event_id": fake.random_element(elements=[event["id"] for event in events]),
            "worker_id": fake.random_element(elements=[worker["id"] for worker in workers]),
            "account_manager_only": fake.boolean(chance_of_getting_true=20),
            "account_manager_and_td_only": fake.boolean(chance_of_getting_true=20)
        }
        notes.append(note)
    return notes

workers = generate_workers()
locations = generate_locations()
events = generate_events(workers=workers, locations=locations)
crews = generate_crew(events=events)
expenses = generate_expenses(workers=workers, events=events)
shifts = generate_shifts(workers=workers, events=events)
notes = generate_notes(workers=workers, events=events)

data = {
    "workers": workers,
    "locations": locations,
    "events": events,
    "crews": crews,
    "expenses": expenses,
    "shifts": shifts,
    "notes": notes
}

with open('seed_data.json', 'w') as f:
    json.dump(data, f, indent=4)
