from pydantic import BaseModel

class RescheduleInput(BaseModel):
    teacherName: str
    courseName: str
    discipline: str
    section: str
    old_Day: str
    old_class_start_time: str
    old_class_end_time: str
    new_Day: str
    new_class_start_time: str
    new_class_end_time: str

class RescheduleModel(BaseModel):
    teacherId:str
    courseId:str
    venueId:str
    old_schedule_id:int
    new_venue_id:str
    start_time:str
    end_time:str
    reschedule:bool
    Day:str
