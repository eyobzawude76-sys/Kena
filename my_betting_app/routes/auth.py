from fastapi import APIRouter, HTTPException, Depends
from ..database import db
from ..models import Agent

router = APIRouter()

# 1. LOG IN (DATABASE IRRAA AGENT BARBAADUU)
@router.post("/login")
async def login(user: Agent):
    # MongoDB keessaa agent username kanaan jiru barbaaduu
    db_user = await db.agents.find_one({"username": user.username})
    
    if not db_user:
        # Yoo kassa keessatti hin argamne, admin database keessa barbaadna
        db_admin = await db.admins.find_one({"username": user.username})
        if db_admin and db_admin["password"] == user.password:
            return {"message": "Login milkiidhaan raawwatameera!", "role": "admin", "agentId": str(db_admin["_id"])}
        raise HTTPException(status_code=401, detail="Maqaa ykn Password dogoggoraa!")
        
    if db_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="Maqaa ykn Password dogoggoraa!")
        
    return {
        "message": "Login milkiidhaan raawwatameera!", 
        "role": "agent", 
        "agentId": str(db_user["_id"]) # ID isaa frontend-iif kennuuf
    }

# 2. AGENT HAARAA REGISTER GOCHUU (ADMIN-OOTAAN FAYYADAMAMA)
@router.post("/register")
async def register_agent(agent: Agent):
    # Username duraan jiriachuu isaa check gochuu
    existing_user = await db.agents.find_one({"username": agent.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Maqaan kassa kanaa duraan galmaa'eera!")
        
    new_agent = agent.dict()
    await db.agents.insert_one(new_agent)
    return {"message": "✅ Agent haaraan milkiidhaan uumameera!"}
@router.get("/agents")
async def get_all_agents():
    agents = []
    # Database keessaa kassaawwan jiran hunda fiduu
    async for agent in db.agents.find():
        agent["_id"] = str(agent["_id"]) # MongoDB ObjectId gara string-itti jijjiiruu
        agents.append(agent)
    return agents

