from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import agents
from personas import get_all_personas
import asyncio

app = FastAPI(title="AI Judge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend'den gelecek verinin modeli
class ReviewRequest(BaseModel):
    code: str
    user_prompt: str = ""
    agent_ids: List[str] = []

@app.get("/personas")
def get_personas():
    all_personas = get_all_personas()
    # Sadece meta datayı dönüyoruz, uzun promptları göndermiyoruz
    return {"status": "success", "personas": {k: v["meta"] for k, v in all_personas.items()}}

@app.get("/")
def read_root():
    return {"status": "success", "message": "AI Judge Backend Hazır."}

@app.post("/analyze")
async def analyze_code(request: ReviewRequest):
    if request.user_prompt:
        # Karar verici ajanı çalıştır
        all_personas = get_all_personas()
        chosen_agents = await asyncio.to_thread(
            agents.run_decision_maker, 
            request.user_prompt, 
            request.code, 
            all_personas
        )
        request.agent_ids = chosen_agents

    if not request.agent_ids:
        return {"status": "error", "message": "En az bir ajan seçilmelidir veya geçerli bir prompt girilmelidir."}

    # Hackathon hilesi: Ajanları aynı anda (paralel) koşturarak bekleme süresini yarıya indiriyoruz!
    tasks = [asyncio.to_thread(agents.run_agent, agent_id, request.code) for agent_id in request.agent_ids]
    
    reports = await asyncio.gather(*tasks)

    # Sonuçları ajan ID'sine göre eşleştir (Sıralamayı korumak önemli)
    boards_result = {agent_id: report for agent_id, report in zip(request.agent_ids, reports)}

    return {
        "status": "success",
        "boards": boards_result,
        "ordered_agents": request.agent_ids
    }