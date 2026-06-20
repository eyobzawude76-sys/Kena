from pydantic import BaseModel,Field
from typing import List, Optional
from datetime import datetime
class TicketCreate(BaseModel):
    agentId: str
    betType: str
    dogs: List[int]
    stake: float
class TicketInDB(BaseModel):
    Id: str
    status: str = "pending"
    potentiallpayout: float
    createdAt:datetime=Field(default_factory=datetime.utcnow)
class Agent(BaseModel):
    username: str
    password: str # Hashing booda itti daballa
    branch: str
    status: str = "Active"


class Dog(BaseModel):
 name:str
 age:int
 best_time:float
 odds:float