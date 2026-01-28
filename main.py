from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from Routes import Admin,Datacell, Teachers,Student,auth
from FaceRecognition import faceRecognition


app=FastAPI(title="MEYE Pro")
app.mount("/Assetes", StaticFiles(directory="Assetes"), name="static")

@app.get("/")
def root():
    return {"Message":"MEYE Pro API is Running on Port 8000"}
app.include_router(auth.router)
app.include_router(Student.router)
app.include_router(Teachers.router)
app.include_router(Admin.router)
app.include_router(Datacell.route)
app.include_router(faceRecognition.router)