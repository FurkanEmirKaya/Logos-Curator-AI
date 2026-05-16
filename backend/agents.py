import os
import json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from personas import get_persona

# .env dosyasındaki API keyleri yükle
load_dotenv()

# Hackathon hızına uygun ve güçlü bir model (OpenAI kullanıyorsan). 
# Alternatif olarak ChatAnthropic veya ChatGoogleGenerativeAI da kullanılabilir.
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def run_agent(persona_id: str, code_input: str) -> str:
    persona = get_persona(persona_id)
    # Gemini 1.5 Pro requires a higher tier, so we use gemini-1.5-flash for the fast analysis
    # The roadmap says Gemini 1.5 Pro for Maker Bot, but flash for fast personas. We will use the defined llm.
    prompt = ChatPromptTemplate.from_messages([
        ("system", persona["prompt"]),
        ("user", "Aşağıdaki konsepti/kodu incele ve raporunu sun:\n\n{code}")
    ])
    chain = prompt | llm
    return chain.invoke({"code": code_input}).content

def run_decision_maker(user_prompt: str, code_input: str, available_personas: dict) -> list[str]:
    persona_descriptions = "\n".join([f"- {pid}: {val['meta']['display_name']} ({val['meta']['role']}) - Uzmanlık: {', '.join(val['meta']['expertise'])}" for pid, val in available_personas.items()])
    
    system_prompt = f"""Sen AI Judge platformunun Baş Karar Vericisisin (Decision Maker).
Görevin, kullanıcının talebini ve sağladığı kodu analiz ederek, bu kodu incelemek için en uygun uzman (ajan) takımını kurmak ve inceleme sırasını belirlemektir.

Mevcut Uzmanlar:
{persona_descriptions}

Kullanıcı Talebi: "{user_prompt}"

Kurallar:
1. Kullanıcının talebine en uygun uzmanları seç. Örneğin sadece "frontend" veya "UI" diyorsa, ilgili uzmanları seç. Eğer genel bir inceleme istiyorsa daha geniş bir takım kur (en fazla 4 kişi).
2. Uzmanları, inceleme yapmaları gereken mantıksal sıraya göre diz.
3. Çıktın KESİNLİKLE VE SADECE geçerli bir JSON array olmalıdır. İçerisinde seçtiğin ajanların ID'leri olmalı. Başka hiçbir açıklama, markdown veya text içermemelidir.

Örnek Çıktı:
["socrates", "alan_turing"]
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Kod:\n\n{code}")
    ])
    chain = prompt | llm
    result = chain.invoke({"code": code_input}).content
    
    result = result.strip()
    if result.startswith("```json"): result = result[7:]
    if result.startswith("```"): result = result[3:]
    if result.endswith("```"): result = result[:-3]
    
    try:
        selected_agents = json.loads(result.strip())
        if not isinstance(selected_agents, list) or len(selected_agents) == 0:
            selected_agents = ["socrates", "alan_turing"]
    except Exception as e:
        print("JSON parse hatası:", e)
        selected_agents = ["socrates", "alan_turing"]
        
    return selected_agents