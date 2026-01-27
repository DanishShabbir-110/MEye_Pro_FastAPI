from pydantic import BaseModel

class AllocationInput(BaseModel):
    courseName: str
    teacherName: str
    discipline: str
    session: str
    section: str
    semester: int

    class Config:
        from_attributes = True