from fastapi import APIRouter, HTTPException
from ..database import db
from bson import ObjectId

router = APIRouter()

@router.get("/agent/{agent_id}")
async def get_agent_report(agent_id: str):
    try:
        # 1. Tikkeettii agent kanaan gurguraman hunda fidi (Canceled kan hin taane)
        all_tickets = await db.tickets.find({"agentId": agent_id}).to_list(length=1000)
        
        total_sales = 0
        total_payout = 0
        recent_tickets = []

        for ticket in all_tickets:
            # Tikkeettii gurgurame (Canceled yoo ta'e herrega keessaa baha)
            if ticket.get("status") != "Canceled":
                total_sales += ticket.get("stake", 0)
            
            # Tikkeettii kaffaltiin irratti raawwate (Paid)
            if ticket.get("status") == "Paid":
                # Kaffaltii dhabataa ta'e ykn potential payout isa ddb jiru fudhanna
                total_payout += ticket.get("potentialPayout", 0)

            # JSON serializer akka hin gufanne _id gara string'tti jijjiirra
            ticket["_id"] = str(ticket["_id"])
            recent_tickets.append(ticket)

        # Net Cash = Sales - Payout
        net_cash = total_sales - total_payout

        # Tikkeettii dhiyoo kutame dhumarratti dhufe akka dursuuf reverse goona
        recent_tickets.reverse()

        return {
            "reports": {
                "totalSales": total_sales,
                "totalPayout": total_payout,
                "netCash": net_cash
            },
            "recent_tickets": recent_tickets[:10]  # Tikkeettii 10 qofa frentend'f ergina
        }

    except Exception as e:
        raise HTTPException(status_code=505, detail=f"Gabaasa fiduun hin danda'amne: {str(e)}")