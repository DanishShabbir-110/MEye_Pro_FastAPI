from typing import List
from pydantic import BaseModel

class TeacherCHRInput(BaseModel):
    teacherName: str
    courseName: str
    discipline: str
    section: str
    venue: str
    date: str
    day: str
    time_in: str
    time_out: str
    stand_time: str
    sit_time: str
    class_start_time: str
    class_end_time: str
    status: str

    
class TeacherCHR(BaseModel):
    scheduleId:int
    date:str
    time_in:str
    time_out:str
    stand_time:str
    sit_time:str
    status:str
    claim:bool

class TeacherCHRReport(BaseModel):
    TeacherName: str
    CourseName: str
    Section: str
    Discipline: str
    Date: str
    StandTime: str
    SitTime: str

class TeacherCHRReportItem(BaseModel):
    Discipline: str
    Date: str
    Course: str
    Day: str
    Class_time: str
    Time_in: str
    Time_out: str
    Status: str

class TeacherCHRResponse(BaseModel):
    Teacher_ID: str
    CHR_Reports: List[TeacherCHRReportItem]    
