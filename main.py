from fastapi import FastAPI
from Routes import Admin,Datacell, Teachers,Student



app=FastAPI(title="MEYE Pro")
@app.get("/")
def root():
    return {"Message":"MEYE Pro API is Running on Port 8000"}
app.include_router(Student.router)
app.include_router(Teachers.router)
app.include_router(Admin.router)
app.include_router(Datacell.route)
