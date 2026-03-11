from pydantic import BaseModel

class LoginRequest(BaseModel):
    nickname: str

class SendMessage(BaseModel):
    session_id:str
    user_id: str
    content: str

