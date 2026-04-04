from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from db import engine, db_manager
from routers import auth, chat, loadmap

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_manager.connect()
    app.state.db = db_manager.db
    yield
    db_manager.close()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "https://your-domain.com",       # todo: 도메인 구입 후 추가
    "https://www.your-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(loadmap.router)

@app.get("/")
def index():
    return "hello"
