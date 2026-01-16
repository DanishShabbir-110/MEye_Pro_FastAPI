from pydantic import BaseModel


class Student(BaseModel):
    Regno:str
    Discipline:str