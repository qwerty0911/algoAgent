from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_ACCESS_URL = os.getenv("MONGODB_ACCESS_URL")

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self):
        # uuidRepresentation 설정을 여기서 한 번에 관리
        self.client = AsyncIOMotorClient(
            os.getenv("MONGODB_ACCESS_URL"),
            uuidRepresentation="standard"
        )
        self.db = self.client.get_database("Databases")
        print("✅ MongoDB Connected")

    def close(self):
        if self.client:
            self.client.close()
            print("❌ MongoDB Disconnected")

# 싱글톤 객체 생성
db_manager = MongoDB()