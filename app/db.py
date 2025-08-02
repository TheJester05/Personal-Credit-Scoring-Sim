
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")  # fallback to localhost
client = AsyncIOMotorClient(MONGO_URI)

db = client["credit_sim_db"]
users_collection = db["users"]
