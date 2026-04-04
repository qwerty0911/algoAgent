import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import get_db
from models import User
from schemas import LoginRequest

router = APIRouter()

@router.post("/login")
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    user_nickname = data.nickname
    db_user = db.query(User).filter(User.nickname == user_nickname).first()

    if not db_user:
        db_user = User(nickname=user_nickname)
        db.add(db_user)
    else:
        db_user.last_login = datetime.datetime.now()

    try:
        db.commit()
        db.refresh(db_user)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database update failed"
        )

    return db_user
