import os
from fastapi import FastAPI, Depends, HTTPException, status
from openai import OpenAI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from models import *
from database import get_db, Base, engine
from schemas import *
import models
from uuid import UUID

app = FastAPI()

# 환경 변수에 따라 허용할 도메인을 변경할 수 있게 기획하면 좋습니다.
# 로컬 테스트시는 localhost, 배포 시에는 실제 도메인 사용
origins = [
    "http://localhost:5173",        # 로컬 리액트 개발 서버
    "https://your-domain.com",      # 실제 배포될 프론트엔드 도메인(todo:도메인 구입후 추가)
    "https://www.your-domain.com",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#model 객체 확인후 db 생성
models.Base.metadata.create_all(bind=engine)
# client = OpenAI()

load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")

# response = client.responses.create(
#     model="gpt-5-nano",
#     input="에이전트란건 뭐야"
# )


@app.get("/")
def index():
    return 'hello'

# @app.get("/gpt")
# def gpt():

#     response = client.responses.create(
#     model="gpt-5-nano",
#     input="에이전트란건 뭐야"
#     )
#     return response.output_text

@app.post("/login")
def login_user(data: LoginRequest, db: Session = Depends(get_db)):

    user_nickname = data.nickname

    db_user = db.query(User).filter(User.nickname == user_nickname).first()
    
    #새 유저
    if not db_user:
        db_user = User(nickname=user_nickname)
        db.add(db_user)

    #기존 유저일 때  
    else:
        db_user.last_login = datetime.now()

    try:
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database update failed"
        )
    
    return db_user

@app.post("/sendmessage")
def login_user(data: SendMessage, db: Session = Depends(get_db)):
    
    user_id = UUID(data.user_id)
    session_id = UUID(data.session_id)
    content = data.content
    
    db_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    
    #첫 메시지일경우
    if not db_session:
        #title은 첫 채팅 후 content 기반으로 AI가 추천해서 넣도록 변경 예정 
        new_session = ChatSession(session_id=session_id, title="새 채팅",user_id=user_id)
        db.add(new_session)
        #메시지를 넣기 전에 세션이 존재함을 DB에 알림
        db.flush()

    new_message = Message(session_id=session_id, content=content, role="user")
    db.add(new_message)
    #TO-DO agent의 답장을 만들어야함

    try:
        db.commit()
        db.refresh(new_message) # 생성된 message_id 등을 다시 읽어옴
    except Exception as e:
        db.rollback()
        print(f"Error detail: {e}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database update failed: {str(e)}"
        )
    
    return new_message