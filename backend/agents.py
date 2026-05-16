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

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview")

# ─────────────────────────────────────────
# Yardımcı: LLM çıktısını string'e dönüştür
# ─────────────────────────────────────────
def _to_str(result) -> str:
    if isinstance(result, list):
        return "".join(block.get("text", "") if isinstance(block, dict) else str(block) for block in result)
    return str(result)

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
) -> str:
    persona       = get_persona(persona_id)
    system_prompt = persona["prompt"]

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

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Aşağıdaki konsepti/kodu incele ve raporunu sun:\n\n{code}"),
    ]) | llm
    return _to_str(chain.invoke({"code": code_input}).content)


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

    system_prompt = """Sen deneyimli bir yazılım mimarısın. Sana bir kod tabanı verilecek.

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
[Dikkat çekici mimari tercihler (monolith/mikro servis, REST/WebSocket vb.)]"""

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Kod tabanı:\n\n{code}"),
    ]) | llm
    return _to_str(chain.invoke({"code": code_input}).content)


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

    system_prompt = f"""Sen deneyimli bir yazılım mimarısın.

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
[Her takımın inceleyeceği alanların kısa özeti]"""

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Kod tabanı:\n\n{code}"),
    ]) | llm
    return _to_str(chain.invoke({"code": code_input}).content)


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

    system_prompt = f"""Sen AI Judge platformunun Baş Karar Vericisisin (Orchestrator).
Görevin, kullanıcının talebini ve projeyi analiz ederek en uygun İnceleme Takımlarını kurmaktır.

Mevcut Uzmanlar:
{persona_descriptions}

Kullanıcı Talebi: "{user_prompt}"

Kurallar:
1. İhtiyaca göre gerektiği kadar takım kur (Frontend, Backend, Güvenlik vb.)
2. Her takıma en fazla 3 üye ata.
3. Her takım için net bir "focus_area" belirle — ajanlar bu sınır dışına çıkmamalıdır.
4. Dizideki sıra = koşturulma sırası. Bağımlılığı olan takımı öne koy.
5. Çıktın KESİNLİKLE SADECE geçerli bir JSON array olmalıdır:

[
  {{
    "name": "Takım İsmi",
    "focus_area": "Odak alanının detaylı tanımı",
    "members": ["persona_id_1", "persona_id_2"]
  }}
]"""

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
        ("user", "Kod Özeti:\n\n{code}"),
    ]) | llm
    result = _strip_md_fence(_to_str(chain.invoke({"code": code_input}).content))

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

    system_prompt = f"""Sen AI Judge platformunda '{team_name}' takımının Moderatörüsün.
Ajanların Odak Alanı: {focus_area}

Görevin: Ajan raporlarını inceleyip ciddi çelişki olup olmadığını belirlemek.
- "A güvenli" ↔ "Güvenlik açığı var" → çelişki
- Farklı eksikliklere odaklanmış ama çelişmeyen raporlar → uzlaşma

ÇIKTIN SADECE AŞAĞIDAKİ JSON OLMALIDIR:
{{
  "consensus_reached": true,
  "feedback": "Uzlaşılmadıysa: çelişkileri çözmek için kısa direktif. Uzlaşıldıysa: boş bırak.",
  "synthesis": "Takımın ortak kararının kısa özeti."
}}"""

    chain  = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Ajan Raporları:\n\n{reports}"),
    ]) | llm
    result = _strip_md_fence(_to_str(chain.invoke({"reports": reports_text}).content))

    try:
        data = json.loads(result)
        data.setdefault("consensus_reached", True)
        return data
    except Exception as e:
        print("Konsensüs Denetçisi — JSON parse hatası:", e)
        return {"consensus_reached": True, "feedback": "", "synthesis": "Uzlaşma sağlandı (fallback)."}


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

    system_prompt = f"""Sen AI Judge platformunun Orkestratör Ajanısın.
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
[Bu talimatlar uygulandığında ne değişmiş olmalı]"""

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", f"Takım Uzlaşma Özeti: {final_synthesis}\n\nTakım Raporları:\n\n{{reports}}"),
    ]) | llm
    return _to_str(chain.invoke({"reports": reports_text}).content)


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

    system_prompt = """Sen AI Judge platformunun Maker Bot'usun (Uygulayıcı).
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
[Diğer dosyalara etkisi, dikkat edilecekler]""" + context_block

    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", f"Takım: {team_name}\n\nTalimatlar:\n\n{{brief}}"),
    ]) | llm
    return _to_str(chain.invoke({"brief": team_brief}).content)