from DB_Setup.getDatabase import get_db
from fastapi import APIRouter, Depends, Form, HTTPException
import pyodbc

router=APIRouter(prefix="/Authorization",tags=["Authorization"])

@router.post("/Login")
def login(
    userId:str=Form(...),
    password:str=Form(...),
    conn:pyodbc.Connection=Depends(get_db)
):
    if conn is None:
        return {"Error": "connection not built"}
    try:
        cursor=conn.cursor()
        cursor.execute("Select Role,Password from [User] where UID = ?",(userId,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Incorrect UserId")
        db_role=row[0]
        db_password=row[1]
        if password==db_password:
            return {"Role":db_role}
        else:
            raise HTTPException(status_code=401,detail="Incorrect Password")
    except HTTPException as he:
        raise he
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        cursor.close()