import os
from motor.motor_asyncio import AsyncIOMotorClient

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self):
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

db_manager = MongoDB()
