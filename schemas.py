from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

#로그인할때
class LoginRequest(BaseModel):
    nickname: str

#client -> server 메시지
class SendMessage(BaseModel):
    session_id:str
    user_id: str
    content: str

#server -> client 세션 리스트
class SessionListResponse(BaseModel):
    session_id : UUID
    title : str

#server -> client 메시지 리스트
class MessageListResponse(BaseModel):
    session_id : UUID
    content : str
    message_id : int
    create_at : datetime

    class Config:
        # SQLAlchemy 객체를 Pydantic 모델로 자동 변환하기 위한 설정 (v2는 from_attributes)
        from_attributes = True

