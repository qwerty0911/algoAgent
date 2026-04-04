from uuid import UUID
from fastapi import APIRouter
from schemas import Problem
from db import db_manager

router = APIRouter()

@router.get("/getLoadmap", response_model=list[Problem])
async def get_loadmap(session_id: str):
    session_uuid = UUID(session_id)
    collection = db_manager.db.get_collection("algoAgent")
    doc = await collection.find_one({"_id": session_uuid})
    if not doc:
        return []
    return doc.get("problems", [])
