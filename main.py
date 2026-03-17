import os
from fastapi import FastAPI, Depends, HTTPException, status
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from langchain.tools import tool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from models import *
from database import get_db, Base, engine
from schemas import *
import models
from uuid import UUID
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model
from tools import *

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

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 알고리즘 학습을 돕는 유능한 멘토입니다."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="chat_history"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

model = init_chat_model("gpt-5-nano")

tools=[fetch_beakjoon]

agent = create_tool_calling_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)



@app.get("/")
def index():
    return 'hello'

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
def send_message(data: SendMessage, db: Session = Depends(get_db)):
    
    user_id = UUID(data.user_id)
    session_id = UUID(data.session_id)
    content = data.content
    
    request_message = Message(session_id=session_id, content=content, role="user")
    
    db_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()

    #1. 세션이 없으면 새로 생성 (첫 대화)
    is_new_session = False
    if not db_session:
        is_new_session = True
        new_session = ChatSession(session_id=session_id, title="새 대화",user_id=user_id)
        db.add(new_session)
        db.flush()

    if is_new_session:
        pass
        # LLM을 호출하여 제목 추출
        # summary_title = quick_title_gen(content)
        # session_obj = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        # session_obj.title = summary_title
    
    #config = {"configurable": {"session_id": session_id}}
    response = agent_executor.invoke(
        {"input": content,
         "chat_history": [] 
        }
        )
    response_message = Message(session_id=session_id, content=response['output'], role="assistant")
    db.add_all([request_message,response_message])

    try:
        db.commit()
        db.refresh(response_message)
    except Exception as e:
        db.rollback()
        print(f"Error detail: {e}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database update failed: {str(e)}"
        )
    
    return response_message

#이전 채팅의 채팅 세션 load
@app.get("/getsessions", response_model=list[SessionListResponse])
def get_sessions(user_id:str, db: Session = Depends(get_db)):

    user_uuid = UUID(user_id)
    db_sessions = db.query(ChatSession).filter(ChatSession.user_id == user_uuid).all()

    return db_sessions;

#이전 채팅 메시지 load
@app.get("/getMessages", response_model=list[MessageListResponse])
def get_messages(session_id:str, db: Session = Depends(get_db)):

    session_uuid = UUID(session_id)
    db_messages = db.query(Message).filter(Message.session_id == session_uuid).all()

    return db_messages;
