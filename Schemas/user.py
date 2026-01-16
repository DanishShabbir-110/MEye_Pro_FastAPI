from datetime import date,time
from pydantic import BaseModel


class User(BaseModel):
    UID:str
    Full_Name:str
    Password:str
    Role:str
    Profile_Image_Url:str
    Profile_Created_Time:time
    Profile_Created_Date:date