import os
from fastapi import FastAPI, Depends, HTTPException, status
from openai import OpenAI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from models import *
from database import get_db, Base, engine
from schemas import *
import models
from uuid import UUID

app = FastAPI()

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
        db.flush()

    request_message = Message(session_id=session_id, content=content, role="user")
    #TO-DO agent의 답장을 만들어야함
    response_message = Message(session_id=session_id, content="AI의 답변입니다."+content, role="assistant")

    db.add_all([request_message,response_message])


    try:
        db.commit()
        db.refresh(request_message)
    except Exception as e:
        db.rollback()
        print(f"Error detail: {e}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database update failed: {str(e)}"
        )
    
    return response_message


@app.get("/getsessions", response_model=list[SessionListResponse])
def get_sessions(user_id:str, db: Session = Depends(get_db)):

    user_uuid = UUID(user_id)
    db_sessions = db.query(ChatSession).filter(ChatSession.user_id == user_uuid).all()

    return db_sessions;

@app.get("/getMessages", response_model=list[MessageListResponse])
def get_messages(session_id:str, db: Session = Depends(get_db)):

    session_uuid = UUID(session_id)
    db_messages = db.query(Message).filter(Message.session_id == session_uuid).all()

    return db_messages;