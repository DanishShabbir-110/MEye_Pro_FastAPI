from DB_Setup.connection import get_connection


def get_db():
    conn = get_connection()
    if conn is None:
        raise Exception("Database connection failed")
    try:
        yield conn
    finally:
        conn.close()