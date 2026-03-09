import os
from fastapi import FastAPI, Depends, HTTPException
from openai import OpenAI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from models import User
from database import get_db, Base, engine
import models
import uuid

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
client = OpenAI()

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

response = client.responses.create(
    model="gpt-5-nano",
    input="에이전트란건 뭐야"
)


@app.get("/")
def index():
    return 'hello'

@app.get("/gpt")
def gpt():

    response = client.responses.create(
    model="gpt-5-nano",
    input="에이전트란건 뭐야"
    )
    return response.output_text

@app.post("/users/")
def create_user(user_id: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    
    new_user = User(user_id=user_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# @app.post("/testMessage")
# def testMessage():

#     messages = {"message": "Hello World \\ 테스트를 위한 메시지입니다.","reply":"테스트를 위한 메시지입니다 이 메시지가 떴다면 성공입니다."}

#     return messages