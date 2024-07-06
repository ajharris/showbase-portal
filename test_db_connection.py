import os
from sqlalchemy import create_engine

def test_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not set")
        return

    try:
        engine = create_engine(database_url)
        connection = engine.connect()
        print("Connected to the database successfully")
        connection.close()
    except Exception as e:
        print(f"Error connecting to the database: {e}")

if __name__ == "__main__":
    test_connection()
