# database.py
import urllib.parse
from sqlalchemy import create_engine, text

SERVER = r"PRATHYUSHA\SQLEXPRESS"
DATABASE = "BikeStores"

odbc_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

params = urllib.parse.quote_plus(odbc_str)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

def get_user(email):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM dbo.app_users WHERE email = :email"),
            {"email": email}
        ).mappings().first()
    return row
