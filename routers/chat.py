from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import get_db
from models import ChatSession, Message
from schemas import SendMessage, SessionListResponse, MessageListResponse, StudySession
from db import db_manager
from agent_context import agent_session_id_ctx
from agent import agent_executor, title_chain

router = APIRouter()

@router.post("/sendmessage")
async def send_message(data: SendMessage, db: Session = Depends(get_db)):
    user_id = UUID(data.user_id)
    session_id = UUID(data.session_id)
    content = data.content

    request_message = Message(session_id=session_id, content=content, role="user")

    db_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()

    if not db_session:
        new_session = ChatSession(session_id=session_id, title="새 대화", user_id=user_id)
        db.add(new_session)
        db.flush()

        new_title = await title_chain.ainvoke({"input": content})
        new_session.title = new_title.strip()[:50]

        mongo_session = StudySession(user_id=user_id, session_id=session_id)
        session_dict = mongo_session.model_dump(by_alias=True)
        collection = db_manager.db.get_collection("algoAgent")
        await collection.insert_one(session_dict)

    token = agent_session_id_ctx.set(session_id)
    try:
        response = await agent_executor.ainvoke(
            {"input": content, "chat_history": []},
            {"metadata": {"session_id": session_id}},
        )
    finally:
        agent_session_id_ctx.reset(token)

    response_message = Message(session_id=session_id, content=response["output"], role="assistant")
    db.add_all([request_message, response_message])

    try:
        db.commit()
        db.refresh(response_message)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database update failed: {str(e)}"
        )

    return response_message


@router.get("/getsessions", response_model=list[SessionListResponse])
def get_sessions(user_id: str, db: Session = Depends(get_db)):
    user_uuid = UUID(user_id)
    return db.query(ChatSession).filter(ChatSession.user_id == user_uuid).all()


@router.get("/getMessages", response_model=list[MessageListResponse])
def get_messages(session_id: str, db: Session = Depends(get_db)):
    session_uuid = UUID(session_id)
    return db.query(Message).filter(Message.session_id == session_uuid).all()
