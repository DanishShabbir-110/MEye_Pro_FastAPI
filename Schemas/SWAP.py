from pydantic import BaseModel


class SwapModelInput(BaseModel):
    teacherAName: str
    teacherBName: str
    courseAName: str
    courseBName: str
    discipline: str
    section: str
    day: str
    startTime: str
    endTime: str