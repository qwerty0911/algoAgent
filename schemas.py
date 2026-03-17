from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, Literal
from dataclasses import dataclass

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
    created_at : datetime
    role : str

    class Config:
        # SQLAlchemy 객체를 Pydantic 모델로 자동 변환하기 위한 설정 (v2는 from_attributes)
        from_attributes = True

#dataschema
class Algorithm(BaseModel):
    """상세한 알고리즘의 정보."""
    type: str = Field(description="알고리즘의 종류(예: 그리디,DP,유니온파인드 등)")
    rating: int = Field(description="난이도(백준기준으로 브론즈, 실버, 골드, 플래티넘, 다이아, 루비)")

@dataclass
class Context:
    user_name: str

class BackjoonId(BaseModel):
    """사용자의 백준 아이디"""
    backjoon_id: Optional[str] = Field(description="사용자의 백준 아이디")