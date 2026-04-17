from pydantic import BaseModel

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

class DoorAccessRequest(BaseModel):
    password: str