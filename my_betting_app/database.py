from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGO_URL = "mongodb+srv://kena_user:kenapassword123@cluster0.uo74prq.mongodb.net/greyhound_betting_db?retryWrites=true&w=majority"
client = AsyncIOMotorClient(MONGO_URL)
db = client.greyhound_betting_db
