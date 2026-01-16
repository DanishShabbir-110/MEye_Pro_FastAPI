import pyodbc

def get_connection():
    try:
        connection = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=Danish;"
            "DATABASE=M-EYE Pro;"
            "Trusted_Connection=yes;"
        )
        return connection
    except Exception as ex:
        print("Database connection error:", ex)
        return None