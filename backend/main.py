from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Any
import asyncio, sqlite3, json, zipfile, io

import agents
from personas import get_all_personas
from config import (
    MAX_CODE_CHARS, MAX_PROMPT_CHARS, MAX_ITERATIONS, STAGGER_DELAY_SECONDS,
    TEXT_EXTENSIONS, ZIP_SKIP_DIRS, DB_NAME, DEFAULT_TEAM,
    ROLE_TR, EXP_TR,
)

# ─────────────────────────────────────────
# Uygulama & CORS
# ─────────────────────────────────────────
app = FastAPI(title="AI Judge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# Request Modelleri
# ─────────────────────────────────────────
class ReviewRequest(BaseModel):
    code: str = Field(..., max_length=MAX_CODE_CHARS)
    user_prompt: str = Field(default="", max_length=MAX_PROMPT_CHARS)
    agent_ids: List[str] = []

class MakerBotRequest(BaseModel):
    user_prompt: str = Field(default="", max_length=MAX_PROMPT_CHARS)
    teams: List[Any] = []

# ─────────────────────────────────────────
# Yardımcılar
# ─────────────────────────────────────────
def save_analysis_session(user_prompt: str, code: str, teams_data: list):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_prompt TEXT, code TEXT, teams_data TEXT
            )
        """)
        cursor.execute(
            "INSERT INTO sessions (user_prompt, code, teams_data) VALUES (?, ?, ?)",
            (user_prompt, code, json.dumps(teams_data)),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Veritabanı kayıt hatası:", e)

# ─────────────────────────────────────────
# Endpoint'ler
# ─────────────────────────────────────────
@app.get("/")
def read_root():
    return {"status": "success", "message": "AI Judge Backend Hazır."}


@app.get("/personas")
def get_personas():
    """Persona listesini Türkçe etiketlerle döndürür (uzun promptlar gönderilmez)."""
    translated = {}
    for pid, data in get_all_personas().items():
        meta = data["meta"].copy()
        meta["role"]      = ROLE_TR.get(meta["role"], meta["role"])
        meta["expertise"] = [EXP_TR.get(e, e) for e in meta.get("expertise", [])]
        translated[pid] = meta
    return {"status": "success", "personas": translated}


@app.post("/analyze")
async def analyze_code(request: ReviewRequest):
    all_personas = get_all_personas()

    # ── Adım 1: Takımları oluştur ─────────────────────────────────
    if request.user_prompt:
        teams = await asyncio.to_thread(
            agents.run_decision_maker,
            request.user_prompt,
            request.code,
            all_personas,
        )
    else:
        if not request.agent_ids:
            return {"status": "error", "message": "En az bir ajan seçilmelidir veya geçerli bir prompt girilmelidir."}
        teams = [{**DEFAULT_TEAM, "members": request.agent_ids}]

    # ── Adım 2: Proje bağımlılık analizi (dependencies.md) ────────
    dependencies_md = await asyncio.to_thread(
        agents.run_project_analyzer,
        request.code,
    )

    # ── Adım 3: Kod haritası oluştur (codemap.md) ─────────────────
    codemap_md = await asyncio.to_thread(
        agents.run_codemap_generator,
        request.code,
        teams,
        dependencies_md,
    )

    # ── Adım 4: Her takım için codemap'ten ilgili bölümü çıkar ────
    def extract_codemap_for_team(team_name: str, codemap: str) -> str:
        """codemap.md içinde o takımla ilgili satırları filtrele."""
        lines = codemap.splitlines()
        relevant = [l for l in lines if team_name.lower() in l.lower() or l.startswith("#") or l.startswith("|--")]
        return "\n".join(relevant[:40]) if relevant else codemap[:600]

    # ── Adım 5: Takımları sırayla çalıştır ────────────────────────
    async def run_agent_staggered(agent_id, code, focus, feedback, codemap_ctx, deps_ctx, delay):
        if delay > 0:
            await asyncio.sleep(delay)
        return await asyncio.to_thread(
            agents.run_agent,
            agent_id, code, focus, feedback, codemap_ctx, deps_ctx,
        )

    team_results = []
    for team in teams:
        team_name  = team.get("name", "Bilinmeyen Takım")
        focus_area = team.get("focus_area", "")
        members    = team.get("members", [])

        team_codemap = extract_codemap_for_team(team_name, codemap_md)
        deps_summary = dependencies_md[:600]  # İlk 600 karakter özet olarak yeterli

        iteration_history = []
        current_feedback  = ""

        for iteration in range(1, MAX_ITERATIONS + 1):
            tasks = [
                run_agent_staggered(
                    agent_id, request.code, focus_area,
                    current_feedback, team_codemap, deps_summary,
                    idx * STAGGER_DELAY_SECONDS,
                )
                for idx, agent_id in enumerate(members)
            ]
            reports = await asyncio.gather(*tasks)
            member_reports = dict(zip(members, reports))

            consensus_result = (
                await asyncio.to_thread(agents.run_consensus_checker, team_name, member_reports, focus_area)
                if len(members) > 1
                else {"consensus_reached": True, "feedback": "", "synthesis": "Tek kişilik takım."}
            )

            iteration_history.append({
                "iteration": iteration,
                "reports": member_reports,
                "consensus_result": consensus_result,
            })

            if consensus_result.get("consensus_reached", True) or iteration == MAX_ITERATIONS:
                break
            current_feedback = consensus_result.get("feedback", "")

        team_results.append({
            "name": team_name,
            "focus_area": focus_area,
            "iterations": iteration_history,
            "final_synthesis": iteration_history[-1]["consensus_result"].get("synthesis", ""),
            "reports": iteration_history[-1]["reports"],
        })

    # ── Adım 6: Orkestratör — Maker Bot talimatları ───────────────
    for tr in team_results:
        tr["maker_bot_brief"] = await asyncio.to_thread(
            agents.run_orchestrator_summary,
            tr["name"], tr["focus_area"], tr["reports"], tr.get("final_synthesis", ""),
        )

    save_analysis_session(request.user_prompt, request.code, team_results)
    return {
        "status": "success",
        "teams": team_results,
        "dependencies_md": dependencies_md,
        "codemap_md": codemap_md,
    }


@app.post("/maker-bot")
async def run_maker_bot(request: MakerBotRequest):
    """Takım talimatlarını sırayla işler; önceki takımın değişikliklerini bağlam olarak iletir."""
    if not request.teams:
        return {"status": "error", "message": "Maker Bot için analiz verileri gereklidir."}

    team_revisions   = []
    previous_context = ""

    for team in request.teams:
        brief = team.get("maker_bot_brief") or (
            f"# {team.get('name', 'Takım')} Talimatları\n\n"
            f"Odak: {team.get('focus_area', '')}\n\n"
            f"Uzlaşma: {team.get('final_synthesis', '')}"
        )

        revision = await asyncio.to_thread(
            agents.run_maker_bot_for_team,
            brief,
            team.get("name", ""),
            previous_context,
        )

        team_revisions.append({
            "team_name": team.get("name"),
            "brief":     brief,
            "revision":  revision,
        })
        previous_context += f"\n[{team.get('name')}] revizyonu tamamlandı: {revision[:600]}\n---\n"

    return {"status": "success", "team_revisions": team_revisions}


@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Metin dosyaları ve ZIP arşivleri (tam proje yapısıyla) desteklenir."""
    filename = file.filename or ""
    ext      = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    raw      = await file.read()

    # ── ZIP ──────────────────────────────
    if ext == ".zip":
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                all_names     = zf.namelist()
                tree          = "# 📁 Proje Yapısı (ZIP)\n```\n" + "\n".join(all_names) + "\n```\n\n"
                content_parts = [tree]
                total_chars   = len(tree)

                for name in all_names:
                    if total_chars >= MAX_CODE_CHARS:
                        content_parts.append("\n> ⚠️ Karakter limiti aşıldığı için bazı dosyalar kesildi.\n")
                        break
                    if name.endswith("/"):
                        continue
                    file_ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name.split("/")[-1] else ""
                    if file_ext not in TEXT_EXTENSIONS:
                        continue
                    if any(skip in name for skip in ZIP_SKIP_DIRS):
                        continue
                    try:
                        fc = zf.read(name).decode("utf-8", errors="replace")
                        if len(fc) > 3000:
                            fc = fc[:3000] + "\n... [dosya kesildi]"
                        section = f"## `{name}`\n```{file_ext[1:]}\n{fc}\n```\n\n"
                        content_parts.append(section)
                        total_chars += len(section)
                    except Exception:
                        pass

                content    = "".join(content_parts)
                file_count = sum(1 for n in all_names if not n.endswith("/"))
        except Exception as e:
            return {"status": "error", "message": f"ZIP açılamadı: {e}"}

        return {
            "status": "success", "filename": filename, "is_zip": True,
            "content":   content[:MAX_CODE_CHARS],
            "truncated": total_chars > MAX_CODE_CHARS,
            "char_count": min(total_chars, MAX_CODE_CHARS),
            "file_count": file_count,
        }

    # ── Tekil Dosya ──────────────────────
    if ext not in TEXT_EXTENSIONS:
        return {"status": "error", "message": f"Desteklenmeyen dosya türü: {ext}"}

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("latin-1", errors="replace")

    truncated = len(content) > MAX_CODE_CHARS
    return {
        "status": "success", "filename": filename, "is_zip": False,
        "content":   f"# Dosya: {filename}\n\n" + content[:MAX_CODE_CHARS],
        "truncated": truncated,
        "char_count": min(len(content), MAX_CODE_CHARS),
    }