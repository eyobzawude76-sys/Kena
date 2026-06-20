import asyncio
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, tickets, reports
# 🔥 DATABASE WAAMUU (Kutaa tickets keessaa 'db' akka waamtu godhameera)
from .routes.tickets import db 

app = FastAPI(title="Greyhound Racing API & Live Engine")

# CORS eeyyama guutuu (HTTP fi Websocket hundaaf)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GameState:
    def __init__(self):
        self.time_left = 300  
        self.status = "Open"  
        self.results = []     
        self.detailed_results = {}  # 🔥 SAANDUQA BU'AA GOSA BET HUNDAA QABATU
        self.dogs_data = []   
        self.current_video = ""  
        self.active_connections: list[WebSocket] = []

game_state = GameState()

# 🎦 VIIDIYOO FI BU'AA ISAANII
RACE_VIDEOS_DB = [
    
        {  "video_url": "https://res.cloudinary.com/dselkyyep/video/upload/race_3_ikpfib.mp4", 
           "top_3": [2, 5, 6] 
    },
      {  "video_url": "https://res.cloudinary.com/dselkyyep/video/upload/race_4_wzmmdt.mp4", 
           "top_3": [6, 4, 5] 
    },
  {
         "video_url": "https://res.cloudinary.com/dselkyyep/video/upload/race_2_qdo2aq.mp4", 
         "top_3": [3, 4, 5]  },
]

def generate_dogs_for_race():
    names = ["Storm", "Blaze", "Shadow", "Rocket", "Bolt", "Flash"]
    random.shuffle(names)
    dogs = []
    for i in range(1, 7):
        dogs.append({
            "id": i,
            "name": names[i-1],
            "age": random.randint(2, 4),
            "best_time": round(random.uniform(28.1, 29.5), 2),
            "odds": round(random.uniform(1.5, 8.0), 1)
        })
    return dogs

async def broadcast_state():
    payload = {
        "time_left": game_state.time_left,
        "status": game_state.status,
        "results": game_state.results,
        "detailed_results": game_state.detailed_results,  # 🔥 BU'AA GOSA BET HUNDAA UI-F ERGAA
        "dogs_data": game_state.dogs_data,
        "current_video": game_state.current_video  
    }
    for connection in game_state.active_connections:
        try:
            await connection.send_json(payload)
        except Exception:
            if connection in game_state.active_connections:
                game_state.active_connections.remove(connection)

# 🐕 🔥 TIKKEETTII OFUMAAN WON/LOST GOCHUU (GOSA BET 4)
async def check_all_tickets(winning_dogs: list):
    try:
        # Tikkeettii 'Pending' ta'an hundumaa database irraa fidi
        pending_tickets = await db.tickets.find({"status": "Pending"}).to_list(length=1000)
        print(f"🔄 Tikkeettii {len(pending_tickets)} qoramuuf qophaa'anii jiru...")

        for ticket in pending_tickets:
            ticket_id = ticket.get("id")
            bet_type = ticket.get("betType")
            chosen_dogs = ticket.get("dogs", [])

            is_winner = False

            if not chosen_dogs:
                continue

            # 🎯 1. WIN QORUU
            if bet_type == "WIN":
                if chosen_dogs[0] == winning_dogs[0]:
                    is_winner = True

            # 🎯 2. EXACTA QORUU
            elif bet_type == "EXACTA":
                if len(chosen_dogs) >= 2 and chosen_dogs[0] == winning_dogs[0] and chosen_dogs[1] == winning_dogs[1]:
                    is_winner = True

            # 🎯 3. QUINELLA QORUU
            elif bet_type == "QUINELLA":
                if len(chosen_dogs) >= 2 and set(chosen_dogs[:2]) == set(winning_dogs[:2]):
                    is_winner = True

            # 🎯 4. TRIFECTA QORUU
            elif bet_type == "TRIFECTA":
                if (len(chosen_dogs) >= 3 and 
                    chosen_dogs[0] == winning_dogs[0] and 
                    chosen_dogs[1] == winning_dogs[1] and 
                    chosen_dogs[2] == winning_dogs[2]):
                    is_winner = True

            # 📝 STATUS DATABASE IRRATHI UPDATE GOCHUU
            final_status = "Won" if is_winner else "Lost"
            await db.tickets.update_one(
                {"id": ticket_id},
                {"$set": {"status": final_status}}
            )
            print(f"🎫 Tikkeettiin {ticket_id} gara status '{final_status}' tti jijjiirameera.")

    except Exception as e:
        print(f"❌ Dogoggora tikkeettii qoruu irratti uumame: {str(e)}")

# 🔄 THE GAME LOOP
async def run_game_loop():
    while True:
        game_state.dogs_data = generate_dogs_for_race()
        
        selected_race = random.choice(RACE_VIDEOS_DB)
        game_state.current_video = selected_race["video_url"]
        future_results = selected_race["top_3"] 
        
        game_state.time_left = 300
        game_state.status = "Open"
        game_state.results = [] 
        game_state.detailed_results = {}  # Hapsi godhi dorgommii haaraaf
        
        while game_state.time_left > 0:
            await asyncio.sleep(1)
            game_state.time_left -= 1
            if game_state.time_left <= 10:
                game_state.status = "Closed"
            await broadcast_state()

        game_state.status = "Running"
        game_state.time_left = 38
        await broadcast_state()
        
        while game_state.time_left > 0:
            await asyncio.sleep(1)
            game_state.time_left -= 1
            await broadcast_state()
        
        # 🏁 DORgOMMIIN XUMURAMEERA
        game_state.results = future_results  
        game_state.status = "Finished"
        game_state.time_left = 50

        # 🔥 FIX: BU'AA GOSA BET HUNDAA OFUMAAN AKKASITTI HIKKA
        if len(future_results) >= 3:
            r1, r2, r3 = future_results[0], future_results[1], future_results[2]
            game_state.detailed_results = {
                "WIN": f" Dog {r1}",
                "EXACTA": f"{r1} ➔ {r2}",
                "QUINELLA": f"{r1} and {r2}",
                "TRIFECTA": f"{r1} ➔ {r2} ➔ {r3}"
            }

        await broadcast_state()

        # 🔥 Ofumaan tikkeettii hunda database irratti 'Won' ykn 'Lost' godha
        await check_all_tickets(future_results)
        
        while game_state.time_left > 0:
            await asyncio.sleep(1)
            game_state.time_left -= 1
            await broadcast_state()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_game_loop())

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    game_state.active_connections.append(websocket)
    initial_payload = {
        "time_left": game_state.time_left,
        "status": game_state.status,
        "results": game_state.results,
        "detailed_results": game_state.detailed_results,
        "dogs_data": game_state.dogs_data,
        "current_video": game_state.current_video
    }
    try:
        await websocket.send_json(initial_payload)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in game_state.active_connections:
            game_state.active_connections.remove(websocket)
    except Exception:
        if websocket in game_state.active_connections:
            game_state.active_connections.remove(websocket)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

@app.get("/")
async def root():
    return {"message": "👑 Engine is Running!"}
