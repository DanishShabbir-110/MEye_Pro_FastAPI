from fastapi import APIRouter
from DB_Setup.connection import get_connection
from pydantic import BaseModel
from Schemas.user import UserCreate
router=APIRouter()
conn=get_connection()
@router.get("/")
def root():
    return {"API is running!!!"}

@router.get("/allUsers")
def getAllUsers():
    if conn is None:
        return{"Error":"connection not built"}
    cursor=conn.cursor()
    cursor.execute("select id,name,age,email from [User]")
    rows=cursor.fetchall()
    list=[]
    for row in rows:
        list.append({
            "id":row[0],
            "name":row[1],
            "age":row[2],
            "email":row[3]
        })
    conn.close()
    return list

@router.get("/getUserById/{id}")
def getUserbyId(id:int):
    if conn is None:
        return{"Error":"connection not built"}
    cursor=conn.cursor()
    query="select id,name,age,email from [User] where id=?"
    cursor.execute(query,(id))
    row=cursor.fetchone()
    if row:
        return{
            "id":row.id,
            "name":row.name,
            "age":row.age,
            "email":row.email
        }
    else:
        return{
            "Message":"no user found with this id "
        }

@router.post("/addUser")
def addUser(user:UserCreate):
    if conn is None:
        return{"Error":"connection not built"}
    cursor=conn.cursor()
    query=f"insert into [User] (name,age,email) values (?,?,?)"
    cursor.execute(query,(user.name,user.age,user.email))
    conn.commit()
    cursor.close()
    return {"Message":"User Added successfully!!"}

@router.put("/updateUser/{id}")
def updateUser(id:int,user:UserCreate):
    if conn is None:
        return{"Error":"connection not built"}
    cursor=conn.cursor()
    fetch_query="select id,name,age,email from [User] where id=?"
    cursor.execute(fetch_query,(id))
    exist_user=cursor.fetchone()
    if not exist_user:
        return{"Message":"no user found with this id "}
    update_query="update [User] set name=?,age=?,email=? where id=?"
    cursor.execute(update_query,(user.name,user.age,user.email,id))
    conn.commit()
    cursor.close()
    return{"Message":"User Updated Successfully!!"}

@router.delete("/deleteUser/{id}")
def deleteUser(id:int):
    if conn is None:
        return{"Error":"connection not built"}
    cursor=conn.cursor()
    fetch_query="select id,name,age,email from [User] where id=?"
    cursor.execute(fetch_query,(id))
    exist_user=cursor.fetchone()
    if not exist_user:
        return{"Message":"no user found with this id "}
    delete_query="Delete from [User] where id=?"
    cursor.execute(delete_query,(id))
    conn.commit()
    cursor.close()
    return {"Message":"User Deleted Successfully!!"}