from pydantic import BaseModel

class StudentAttendanceModel(BaseModel):
    studentRegno: str
    teacherId: str
    courseName: str
    discipline: str
    section: str
    day: str
    class_start_time: str
    class_end_time: str
    date: str

class StudentAttendanceResponse(BaseModel):
    Message: str
    Student: str


class ClaimAttendanceResponse(BaseModel):
    regno: str
    date: str
    course: str
    message: str