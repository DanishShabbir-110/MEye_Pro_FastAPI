from pydantic import BaseModel


class Student_Pics(BaseModel):
    Pic_id:str
    Pic_url:str
    Regno:str