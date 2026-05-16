import os, json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from personas import get_persona
from config import (
    MAX_DECISION_MAKER_CHARS,
    MAX_ORCHESTRATOR_REPORT_CHARS,
    MAX_MAKER_BOT_CONTEXT_CHARS,    
)

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

class QuotaExceededError(Exception):
    """API kotası dolduğunda fırlatılır."""
    pass

def _safe_invoke(chain, inputs):
    try:
        return chain.invoke(inputs)
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            raise QuotaExceededError("Gemini API kotası doldu. Lütfen 1 dakika bekleyin veya daha yüksek kotalı bir modele (örn: Flash) geçin.")
        raise e

# ─────────────────────────────────────────
# Dinamik Model Güncelleyici
# ─────────────────────────────────────────
_ALLOWED_MODELS = {
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
}

def set_model(model_id: str) -> None:
    """Frontend'den gelen model ID'sine göre global llm'i günceller."""
    global llm
    if model_id in _ALLOWED_MODELS:
        llm = ChatGoogleGenerativeAI(model=model_id)
        print(f"[Model] {model_id} aktif.")
    else:
        print(f"[Model] Geçersiz model '{model_id}', varsayılan kullanılıyor.")

# ─────────────────────────────────────────
# ORCHESTRATOR PROTOCOL (New Core Mission)
# ─────────────────────────────────────────
ORCHESTRATOR_PROTOCOL = """
### 🔴 CRITICAL: ORCHESTRATOR PROTOCOL (SYSTEM-WIDE RULES) 🔴 ###
1. **LANGUAGE PRIORITY**: This rule overrides ALL other instructions, including persona traits. 
   - Detect the language of the user's input.
   - Your final, visible output MUST be in the **EXACT SAME LANGUAGE** as the user's input (e.g., if they write in Turkish, you MUST respond in Turkish).
2. **INTERNAL REASONING**: Conduct all internal chain-of-thought, logical analysis, and technical debates strictly in **ENGLISH**.
3. **FINAL FILTER**: Before presenting your output, perform a self-check: "Is my response in the same language the user used?" If the user input was Turkish and your output is English, you have FAILED. Translate it immediately before delivery.
4. **PRIVACY**: Never expose your internal English reasoning or "thoughts" block to the user. Only show the final persona-appropriate response in their language.
"""

# ─────────────────────────────────────────
# Yardımcı: LLM çıktısını string'e dönüştür
# ─────────────────────────────────────────
def _to_str(result) -> str:
    if isinstance(result, list):
        return "".join(block.get("text", "") if isinstance(block, dict) else str(block) for block in result)
    return str(result)

def _apply_protocol(prompt: str) -> str:
    """Sistem promptuna İngilizce düşünme ve hedef dilde çıktı üretme kuralını ekler."""
    return ORCHESTRATOR_PROTOCOL + "\n\n" + prompt

# ─────────────────────────────────────────
# Yardımcı: Markdown kod bloğu sarmasını temizle
# ─────────────────────────────────────────
def _strip_md_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def _check_and_fix_language(text: str) -> str:
    """Eğer çıktı İngilizce ise ve Türkçe olması gerekiyorsa otomatik çevirir."""
    # Türkçe karakter kontrolü (ğ, ü, ş, ı, ö, ç)
    tr_chars = "ğüşıöçĞÜŞİÖÇ"
    has_tr = any(c in text for c in tr_chars)
    
    # Eğer metin uzunsa ve Türkçe karakter yoksa, İngilizce olma ihtimali yüksektir
    if not has_tr and len(text) > 150:
        en_indicators = [" the ", " and ", " is ", " for ", " with "]
        if any(ind in text.lower() for ind in en_indicators):
            # İngilizce tespit edildi, hızlıca çevir
            fix_chain = ChatPromptTemplate.from_messages([
                ("system", "You are a professional translator. Translate the given text into TURKISH. "
                           "Keep the same style, formatting, and markdown tags."),
                ("user", "{text}"),
            ]) | llm
            return _to_str(_safe_invoke(fix_chain, {"text": text}).content)
    return text

# ─────────────────────────────────────────
# Ajan Çalıştırıcı
# ─────────────────────────────────────────
def run_agent(
    persona_id: str,
    code_input: str,
    focus_area: str = "",
    previous_feedback: str = "",
    codemap_context: str = "",
    dependencies_context: str = "",
    context_summary: str = "",
) -> str:
    persona       = get_persona(persona_id)
    system_prompt = ORCHESTRATOR_PROTOCOL + "\n\n" + persona["prompt"]

    if dependencies_context:
        system_prompt += (
            f"\n\n[PROJE BİLGİSİ — BAĞIMLILIKLAR]: Aşağıdaki proje özeti incelemenize "
            f"bağlam sağlamaktadır. Teknoloji yığınını, hedef kitleyi ve amacı göz önünde bulundurun:\n"
            f"{dependencies_context}"
        )
    if codemap_context:
        system_prompt += (
            f"\n\n[KOD HARİTASI — SİZİN DOSYALARINIZ]: İncelemenizi YALNIZCA aşağıda "
            f"listelenen dosya ve klasörlere odaklayın. Diğer alanlar farklı takımlar tarafından "
            f"ele alınmaktadır:\n{codemap_context}"
        )
    if context_summary:
        system_prompt += (
            f"\n\n[SOHBET / BAĞLAM ÖZETİ]: Devam eden sürecin güncel durumu:\n"
            f"{context_summary}\nLütfen bu özeti kararlarında göz önünde bulundur."
        )
    if focus_area:
        system_prompt += (
            f"\n\n[ODAK ALANI]: Lütfen SADECE şu alana odaklanarak inceleme yap, "
            f"kendi uzmanlığınla ilgili olmayan kısımları yoksay:\n{focus_area}"
        )
    if previous_feedback:
        system_prompt += (
            f"\n\n[İTERASYON BİLGİSİ / GERİ BİLDİRİM]: Önceki turda anlaşmazlıklar "
            f"yaşandı. Moderatörün geri bildirimi:\n'{previous_feedback}'\n"
            f"Lütfen bu geri bildirimi dikkate alarak incelemeni ortak paydaya yaklaştır."
        )

    # Sandwich technique: Reinforce protocol at the end
    system_prompt += (
        f"\n\n### 🔴 FINAL LANGUAGE FILTER 🔴 ###\n"
        f"Even though you are acting as {persona_id}, your output MUST be in TURKISH. "
        f"If your inner reasoning was in English, translate it to Turkish NOW. "
        f"DO NOT deliver the output in English."
    )

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Aşağıdaki konsepti/kodu incele ve raporunu sun:\n\n{code}\n\nCRITICAL: Respond in TURKISH."),
    ]) | llm
    raw_output = _to_str(_safe_invoke(chain, {"code": code_input}).content)
    return _check_and_fix_language(raw_output)


# ─────────────────────────────────────────
# Proje Analisti — dependencies.md üretici
# ─────────────────────────────────────────
def run_project_analyzer(code_input: str) -> str:
    """
    Kod tabanını okuyup projenin temel bağımlılıklarını ve bağlamını
    özetleyen bir dependencies.md içeriği üretir.
    """
    if len(code_input) > MAX_DECISION_MAKER_CHARS:
        half = MAX_DECISION_MAKER_CHARS // 2
        code_input = code_input[:half] + "\n\n...[TOKEN TASARRUFU: ORTA KISIM KESİLDİ]...\n\n" + code_input[-half:]

    system_prompt = _apply_protocol("""Sen deneyimli bir yazılım mimarısın. Sana bir kod tabanı verilecek.

Görevin: Kod tabanını analiz edip aşağıdaki Markdown formatında SADECE şu dosyayı üret:

# 📦 dependencies.md — Proje Bağımlılık ve Bağlam Raporu

## 🎯 Projenin Amacı
[Projenin ne yaptığını 2-3 cümleyle açıkla]

## 👥 Hedef Kitle
[Projenin kimin için yapıldığını belirt]

## 🛠️ Teknoloji Yığını
| Kategori | Teknoloji / Araç |
|----------|------------------|
| Frontend | ... |
| Backend  | ... |
| Veritabanı | ... |
| Diğer    | ... |

## 📌 Temel Özellikler
- [Özellik 1]
- [Özellik 2]

## 🔗 Dış Bağımlılıklar & API'ler
[Kullanılan dış kütüphaneler, API'ler veya servisler]

## ⚡ Mimari Kararlar
[Dikkat çekici mimari tercihler (monolith/mikro servis, REST/WebSocket vb.)]""")

    # Reinforce language
    system_prompt += "\n\nCRITICAL: Output must be in TURKISH."

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Kod tabanı:\n\n{code}\n\nCRITICAL: Respond in TURKISH."),
    ]) | llm
    return _to_str(_safe_invoke(chain, {"code": code_input}).content)


# ─────────────────────────────────────────
# Kod Haritası Üretici — codemap.md
# ─────────────────────────────────────────
def run_codemap_generator(code_input: str, teams: list[dict], dependencies_md: str) -> str:
    """
    Kod tabanını ve oluşturulan takımları bilerek, hangi dosya/klasörün
    hangi takıma ait olduğunu gösteren bir codemap.md üretir.
    """
    if len(code_input) > MAX_DECISION_MAKER_CHARS:
        half = MAX_DECISION_MAKER_CHARS // 2
        code_input = code_input[:half] + "\n\n...[TOKEN TASARRUFU: ORTA KISIM KESİLDİ]...\n\n" + code_input[-half:]

    team_list = "\n".join([f"- {t['name']}: {t['focus_area']}" for t in teams])

    system_prompt = _apply_protocol(f"""Sen deneyimli bir yazılım mimarısın.

Proje bağımlılıkları:
{dependencies_md[:800]}

Oluşturulan inceleme takımları:
{team_list}

Görevin: Kod tabanındaki her önemli dosya ve klasörü, onu inceleyecek takıma atayan
bir codemap.md üret. Her dosya/klasör için kısaca ne işe yaradığını da belirt.

SADECE şu Markdown formatını kullan:

# 🗺️ codemap.md — Kod Haritası

## Dosya / Klasör Atamaları

| Yol | Tür | Takım | Açıklama |
|-----|-----|-------|----------|
| `[dosya_veya_klasör]` | [frontend/backend/config/test/...] | [Takım Adı] | [Ne işe yarar] |

## 📋 Takım Odak Özeti
[Her takımın inceleyeceği alanların kısa özeti]""")

    # Reinforce language
    system_prompt += "\n\nCRITICAL: Output must be in TURKISH."

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Kod tabanı:\n\n{code}\n\nCRITICAL: Respond in TURKISH."),
    ]) | llm
    return _to_str(_safe_invoke(chain, {"code": code_input}).content)


# ─────────────────────────────────────────
# Karar Verici (Orchestrator — Takım Planlayıcı)
# ─────────────────────────────────────────
_FALLBACK_TEAMS = [{"name": "Genel İnceleme Takımı",
                    "focus_area": "Projenin tüm kısımlarını genel olarak analiz et.",
                    "members": ["socrates", "alan_turing"]}]

def run_decision_maker(user_prompt: str, code_input: str, available_personas: dict) -> list[dict]:
    persona_descriptions = "\n".join([
        f"- {pid}: {val['meta']['display_name']} ({val['meta']['role']}) "
        f"- Uzmanlık: {', '.join(val['meta']['expertise'])}"
        for pid, val in available_personas.items()
    ])

    system_prompt = _apply_protocol(f"""Sen AI Judge platformunun Baş Karar Vericisisin (Orchestrator).
Görevin, kullanıcının talebini ve projeyi analiz ederek en uygun İnceleme Takımlarını kurmaktır.

Mevcut Uzmanlar:
{persona_descriptions}

Kullanıcı Talebi: "{user_prompt}"

Kurallar:
1. İhtiyaca göre takımları kur (Örn: Frontend, Backend, Güvenlik). EN FAZLA 3 TAKIM kurabilirsin.
2. Her takıma EN FAZLA 2 üye ata.
3. Her takım için net bir "focus_area" belirle — ajanlar bu sınır dışına çıkmamalıdır.
4. Dizideki sıra = koşturulma sırası. Bağımlılığı olan takımı öne koy.
5. Çıktın KESİNLİKLE SADECE geçerli bir JSON array olmalıdır:

[
  {{{{
    "name": "Takım İsmi",
    "focus_area": "Odak alanının detaylı tanımı",
    "members": ["persona_id_1", "persona_id_2"]
  }}}}
]""")

    # Token tasarrufu: uzun kodun sadece başını ve sonunu gönder
    if len(code_input) > MAX_DECISION_MAKER_CHARS:
        half = MAX_DECISION_MAKER_CHARS // 2
        code_input = (
            code_input[:half]
            + "\n\n...[TOKEN TASARRUFU: ORTA KISIM KESİLDİ]...\n\n"
            + code_input[-half:]
        )

    chain  = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Kod Özeti:\n\n{code}\n\nCRITICAL: Respond in TURKISH."),
    ]) | llm
    result = _strip_md_fence(_to_str(_safe_invoke(chain, {"code": code_input}).content))

    try:
        teams = json.loads(result)
        if not isinstance(teams, list) or len(teams) == 0:
            return _FALLBACK_TEAMS
        return teams
    except Exception as e:
        print("Karar Verici — JSON parse hatası:", e)
        return _FALLBACK_TEAMS


# ─────────────────────────────────────────
# Konsensüs Denetçisi (Moderatör)
# ─────────────────────────────────────────
def run_consensus_checker(team_name: str, reports: dict, focus_area: str) -> dict:
    reports_text = "\n\n".join(
        f"--- {aid} RAPORU ---\n{report}" for aid, report in reports.items()
    )

    system_prompt = _apply_protocol(f"""Sen AI Judge platformunda '{team_name}' takımının Moderatörüsün.
Ajanların Odak Alanı: {focus_area}

Görevin: Ajan raporlarını inceleyip ciddi çelişki olup olmadığını belirlemek.
- "A güvenli" ↔ "Güvenlik açığı var" → çelişki
- Farklı eksikliklere odaklanmış ama çelişmeyen raporlar → uzlaşma

ÇIKTIN SADECE AŞAĞIDAKİ JSON OLMALIDIR:
{{{{
  "consensus_reached": true,
  "feedback": "Uzlaşılmadıysa: çelişkileri çözmek için kısa direktif. Uzlaşıldıysa: boş bırak.",
  "synthesis": "Takımın ortak kararının kısa özeti."
}}}}""")

    chain  = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Ajan Raporları:\n\n{reports}\n\nCRITICAL: Respond in TURKISH."),
    ]) | llm
    raw_result = _strip_md_fence(_to_str(_safe_invoke(chain, {"reports": reports_text}).content))
    
    try:
        data = json.loads(raw_result)
        if data.get("synthesis"):
            data["synthesis"] = _check_and_fix_language(data["synthesis"])
        data.setdefault("consensus_reached", True)
        return data
    except Exception as e:
        print("Konsensüs Denetçisi — JSON parse hatası:", e)
        return {"consensus_reached": True, "feedback": "", "synthesis": "Uzlaşma sağlandı (fallback)."}


# ─────────────────────────────────────────
# Bağlam Özetleyici (Context Summarizer)
# ─────────────────────────────────────────
def run_context_summarizer(previous_summary: str, current_goal: str, latest_events: str) -> str:
    """
    Paralel ajanların token tüketimini azaltmak için sohbet/analiz geçmişini
    ve alınan kararları kompakt bir Markdown dosyası formatında özetler (İngilizce).
    """
    system_prompt = """You are the 'Context Summarizer' agent of the AI Judge platform.
Your task is to maintain a compact, highly efficient Markdown summary of the ongoing analysis/development process.
This summary is used as INTERNAL CONTEXT for other AI agents to save tokens. Therefore, it MUST be in ENGLISH.
If a previous summary exists, integrate the new events into it, updating the status and decisions accordingly.

YOU MUST STRICTLY USE THIS MARKDOWN FORMAT (DO NOT ADD ANY OTHER TEXT):

# CHAT CONTEXT SUMMARY
- **Current Status/Goal:** [The main goal and focus of the ongoing conversation/task]
- **Key Decisions Made:** [Confirmed decisions, agreed-upon solutions so far]
- **Current Constraints:** [User constraints, technical constraints, or rules]
- **Latest Changes/Updates:** [Items added, changed, or fixed in the most recent iteration]
"""

    user_msg = f"Current Goal: {current_goal}\n\n"
    if previous_summary:
        user_msg += f"Previous Summary:\n{previous_summary}\n\n"
    user_msg += f"Latest Events / Decisions / Reports:\n{latest_events}"

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
    ]) | llm
    
    return _strip_md_fence(_to_str(_safe_invoke(chain, {"input": user_msg}).content))


# ─────────────────────────────────────────
# Orkestratör Özeti (Maker Bot için Briefing)
# ─────────────────────────────────────────
def run_orchestrator_summary(team_name: str, focus_area: str, reports: dict, final_synthesis: str) -> str:
    """Takım uzlaşması sonrası Maker Bot için yapılandırılmış bir eylem planı üretir."""
    reports_text = "\n\n".join(
        f"### {aid}:\n{report[:MAX_ORCHESTRATOR_REPORT_CHARS]}"
        + ("..." if len(report) > MAX_ORCHESTRATOR_REPORT_CHARS else "")
        for aid, report in reports.items()
    )

    system_prompt = _apply_protocol(f"""Sen AI Judge platformunun Orkestratör Ajanısın.
'{team_name}' takımı ({focus_area}) uzlaşmaya ulaştı.

Görevin: Takımın raporlarını ve uzlaşma özetini okuyarak Maker Bot için net bir EYLEM PLANI hazırlamak.
Maker Bot bu planı okuyarak kodu doğrudan uygulayacak — soyut değil, somut ve dosya bazında yaz.

ÇIKTIN SADECE ŞU MARKDOWN FORMATI OLMALIDIR:

# 📋 {team_name} — Maker Bot Talimatları

## 🎯 Kapsam
[Bu takımın odak alanını çok kısa özetle]

## ⚡ Eylem Listesi

| Dosya | Yapılacak İşlem | Öncelik |
|-------|-----------------|---------|
| `[dosya_yolu]` | [Net değişiklik] | 🔴 Kritik / 🟡 Yüksek / 🟢 Normal |

## 💻 Kod Düzeyinde Talimatlar
[Somut, uygulanabilir açıklama. Gerekirse kod örneği ekle.]

## ⚠️ Dikkat Edilecekler
[Risk, kısıtlama veya çelişkiler]

## ✅ Başarı Kriterleri
[Bu talimatlar uygulandığında ne değişmiş olmalı]""")

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", f"Takım Uzlaşma Özeti: {final_synthesis}\n\nTakım Raporları:\n\n{{reports}}\n\nCRITICAL: Respond in TURKISH."),
    ]) | llm
    raw_output = _to_str(_safe_invoke(chain, {"reports": reports_text}).content)
    return _check_and_fix_language(raw_output)


# ─────────────────────────────────────────
# Maker Bot (Sıralı Kod Üretici)
# ─────────────────────────────────────────
def run_maker_bot_for_team(team_brief: str, team_name: str, previous_context: str = "") -> str:
    """
    Tek bir takımın talimatlarını alır ve önceki takımların değişikliklerini
    bağlam olarak göz önünde bulundurarak uygulanabilir kod revizyonu üretir.
    """
    context_block = ""
    if previous_context:
        context_block = (
            f"\n\n[BAĞLAM — ÖNCEKİ TAKIM DEĞİŞİKLİKLERİ]: "
            f"Aşağıdaki değişikliklerle çakışma veya tekrar etme:\n"
            f"{previous_context[:MAX_MAKER_BOT_CONTEXT_CHARS]}"
        )

    system_prompt = _apply_protocol("""Sen AI Judge platformunun Maker Bot'usun (Uygulayıcı).
Sana bir takımın talimatları veriliyor. Bu talimatlara göre GERÇEK, UYGULANABİLİR kod üret.

Kurallar:
- Sadece talimatlarda belirtilen dosyalara dokun.
- Değişikliği tam ve çalışabilir kod olarak yaz.
- Hem frontend hem backend'e dokunulması gerekiyorsa her ikisini ayrı bölümlerde göster.
- Yalnızca aşağıdaki Markdown formatını kullan, başka açıklama ekleme.

ÇIKTIN SADECE ŞU FORMAT OLMALIDIR:

## 🔧 [Takım Adı] — Kod Revizyonu

### 📁 Değiştirilen Dosyalar

#### `[dosya/yolu.uzanti]`
**Yapılan Değişiklik:** [Ne değiştirildi — bir cümle]
```[dil]
[Tam, çalışabilir kod bloğu]
```

### 📝 Uygulama Notları
[Diğer dosyalara etkisi, dikkat edilecekler]""") + context_block

    # Reinforce language
    system_prompt += "\n\nCRITICAL: Explanations and notes must be in TURKISH. Code remains in its language."

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", f"Takım: {team_name}\n\nTalimatlar:\n\n{{brief}}\n\nCRITICAL: Explanations in TURKISH."),
    ]) | llm
    return _to_str(_safe_invoke(chain, {"brief": team_brief}).content)


# ─────────────────────────────────────────
# Kod Üreticisi — Mode Bazlı (4 yetenek)
# ─────────────────────────────────────────
_FILE_FMT = """

Her dosya için KESİNLİKLE şu formatı kullan, başka hiçbir metin ekleme:

## 📄 [dosya/yolu.uzantı]
```[dil]
[dosya içeriği]
```
"""

_MODE_PROMPTS: dict[str, str] = {
    "prototipleme": (
        "Sen deneyimli bir full-stack yazılım geliştiricisisin.\n"
        "Kullanıcının açıklamasına göre çalışan, gerçek bir prototip oluştur.\n"
        "Önce README.md yaz, ardından tüm kaynak dosyaları yaz." + _FILE_FMT
    ),
    "versiyon_guncelleme": (
        "Sen deneyimli bir yazılım geliştiricisisin.\n"
        "Verilen kodu belirtilen yeni versiyona/framework'e güncelle.\n"
        "Breaking change'leri düzelt, deprecated API'leri yenisiyle değiştir." + _FILE_FMT
    ),
    "dil_degisikligi": (
        "Sen çok dilli deneyimli bir yazılım geliştiricisisin.\n"
        "Verilen kodu belirtilen hedef dile migrate et.\n"
        "Her dilin idiomlarını kullan, okunabilir ve temiz kod yaz." + _FILE_FMT
    ),
    "sifirdan_uretme": (
        "Sen deneyimli bir yazılım mimarı ve geliştiricisisin.\n"
        "Kullanıcının proje açıklamasına göre eksiksiz, çalışan bir proje oluştur.\n"
        "Önce README.md ve proje yapısını, ardından tüm dosyaları yaz." + _FILE_FMT
    ),
}


def run_code_generator(
    mode: str,
    user_prompt: str,
    code_input: str = "",
    extra_params: dict | None = None,
) -> str:
    """Mode'a göre kod üretir. Çıktı ## 📄 formatında dosya listesidir."""
    if extra_params is None:
        extra_params = {}

    system_prompt = _MODE_PROMPTS.get(mode, _MODE_PROMPTS["prototipleme"])

    # Mode'a özel ek bağlam
    if mode == "versiyon_guncelleme":
        tv = extra_params.get("target_version", "")
        if tv:
            system_prompt += f"\nHedef Versiyon: {tv}"
    elif mode == "dil_degisikligi":
        sl = extra_params.get("source_lang", "")
        tl = extra_params.get("target_lang", "")
        system_prompt += f"\nKaynak Dil: {sl or 'otomatik tespit'}\nHedef Dil: {tl}"
    elif mode == "sifirdan_uretme":
        ts = extra_params.get("tech_stack", "")
        if ts:
            system_prompt += f"\nTercih Edilen Teknoloji Yığını: {ts}"

    system_prompt = _apply_protocol(system_prompt)

    user_message = user_prompt
    if code_input:
        user_message += f"\n\nMevcut Kod:\n{code_input[:MAX_DECISION_MAKER_CHARS * 5]}"

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}\n\nCRITICAL: Explanations in TURKISH."),
    ]) | llm
    return _to_str(_safe_invoke(chain, {"input": user_message}).content)