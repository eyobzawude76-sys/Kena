from fastapi import APIRouter, HTTPException, status
from ..database import db
from ..models import TicketCreate
import random
from datetime import datetime, timezone
import bson

# 🌐 PREFIX KANA DUWWAA GODHI! main.py irratti /api/tickets waan jiruuf
router = APIRouter()

# 🎟️ 1. TIKKEETTII KUTUU
@router.post("/create")
async def create_ticket(ticket: TicketCreate):
    try:
        try:
            await db.tickets.drop_index("qr_code_1")
        except Exception:
            pass
            
        multiplier = 4.5
        potential_payout = ticket.stake * multiplier
        ticket_id = f"TK-{random.randint(10000, 99999)}" 
        
        new_ticket = {
            "id": ticket_id,
            "agentId": ticket.agentId,
            "betType": ticket.betType,
            "dogs": ticket.dogs,
            "stake": ticket.stake,
            "status": "Pending",
            "potentialPayout": potential_payout,
            "createdAt": datetime.now(timezone.utc) 
        }
        
        await db.tickets.insert_one(new_ticket)
        
        new_ticket["_id"] = str(new_ticket["_id"])
        return new_ticket
        
    except Exception as e:
        print(f"❌ ERROR TICKETS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"tickets not: {str(e)}")

# 💰 2. KAFFALTII RAAWWACHUU
# 💰 2. KAFFALTII RAAWWACHUU (PUT /payout/{ticket_id})
@router.put("/payout/{ticket_id}")
async def process_payout(ticket_id: str):
    # 1. Tikkeettii dursa database keessaa fidi (id isaa "TK-XXXX" kanaan)
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="⚠️ tickets not found!")

    # 2. Tikkeettiin sun dursa kan mo'ate (Won) ta'uu isaa mirkaneessi
    if ticket.get("status") != "Won":
        raise HTTPException(
            status_code=400, 
            detail=f"⚠️ Lost: {ticket.get('status')}"
        )

    # 3. Status tikkeettii san gara "Paid" (Kaffalameera) tti jijjiiri
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"status": "Paid"}}
    )
    
    # 📊 4. GABAASA KASSA IRRATTI MAALLAQA PAYOUT DABALUU
    agent_id = ticket.get("agentId")
    payout_amount = ticket.get("potentialPayout", 0) # Maallaqa inni mo'ate
    
    if agent_id and agent_id != "anonymous":
        await db.reports.update_one(
            {"agentId": agent_id},
            {
                "$inc": {
                    "totalPayout": payout_amount,  # Kaffaltiin ni dabalama
                    "netCash": -payout_amount     # Net cash harkaa qabdu ni hir'ata
                }
            },
            upsert=True
        ) 
        
    return {"message": "✅tickets  payout"}
# ❌ 3. TIKKEETTII CANCEL GOCHUU
@router.post("/cancel/{ticket_id}")
async def cancel_ticket(ticket_id: str):
    # 1. Tikkeettii database keessaa fidi
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Not foun ticket")

    if ticket.get("status") == "Canceled":
        raise HTTPException(status_code=400, detail="⚠️ The ticket was cancelled beforehand!")

    # 2. ⏱️ SEERA SEKENDII 15 HERREGUU (TIMEZONE FIX)
    created_at = ticket.get("createdAt")
    if created_at:
        # Yoo string bifa kanaan dhufe gara datetime object-itti jijjiira
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            
        # 🔥 FIX: Lamaanayyuu timezone isaanii qulqulleessinee bifa "Naive" (UTC) goona akka Python unka kanaan walirraa hir'isuuf
        if created_at.tzinfo is not None:
            created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)
            
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        diff_seconds = (now_utc - created_at).total_seconds()

        # To'annoof terminal irratti natti mullisi
        print(f"⏱️ Ticket Time Difference: {diff_seconds} seconds")

        if diff_seconds > 15:
            raise HTTPException(
                status_code=400, 
                detail="After 15 seconds have passed this ticket cannot be cancelled."
            )

    # 3. Tikkeettii haquu (Status Canceled gochuu)
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"status": "Canceled"}}
    )
    
    # 📊 Gabaasa Kassa (totalSales fi netCash) irraa maallaqa hir'isuu
    agent_id = ticket.get("agentId")
    stake_amount = ticket.get("stake", 0)
    
    if agent_id and agent_id != "anonymous":
        await db.reports.update_one(
            {"agentId": agent_id},
            {
                "$inc": {
                    "totalSales": -stake_amount,
                    "netCash": -stake_amount
                }
            },
            upsert=True
        )
    
    return {"message": "The ticket was cancelled successfully"}