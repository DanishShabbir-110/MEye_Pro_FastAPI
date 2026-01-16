from pydantic import BaseModel


class DVRModelInput(BaseModel):
    MAC: str
    IP: str
    Name: str
    channel: int
    Password: str
    admin_id: str