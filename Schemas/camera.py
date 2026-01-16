from pydantic import BaseModel


class CameraModelInput(BaseModel):
    mac: str
    placement: str
    channel_no: int
    resolution: str
    dvr_id: str
    venue_id: str
    IP:str
    status: str = "Active"