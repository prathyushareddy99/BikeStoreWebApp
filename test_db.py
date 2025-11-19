# test_db.py
from database import SessionLocal
from sqlalchemy import text

def test_connection():
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).scalar()
        print("DB test result:", result)
    except Exception as e:
        print("Error while connecting to DB:")
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
