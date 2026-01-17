from pydantic import BaseModel


class SingleEnrollmentInput(BaseModel):
    Regno:str
    courseName:str
    section:str
    semester:int
    session:str