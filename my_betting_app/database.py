from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGO_URL = "mongodb+srv://eyobzawude76_db_user:12357ab%40%23@cluster0.uo74prq.net.mongodb/?retryWrites=true&w=majority"
client = AsyncIOMotorClient(MONGO_URL)
db = client.greyhound_betting_db
