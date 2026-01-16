from pydantic import BaseModel


class PrescheduleModel(BaseModel):
    old_schedule_id:int
    new_venue_id:str
    start_time:str
    end_time:str
    preschedule:bool
    Day:str


class PrescheduleInput(BaseModel):
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
