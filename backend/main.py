from fastapi import FastAPI, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Any, Dict, Optional
import asyncio, sqlite3, json, zipfile, io

import agents
from agents import QuotaExceededError
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
    model: str = Field(default="gemini-2.5-flash")

class MakerBotRequest(BaseModel):
    user_prompt: str = Field(default="", max_length=MAX_PROMPT_CHARS)
    teams: List[Any] = []

class GenerateRequest(BaseModel):
    mode: str
    user_prompt: str = Field(default="", max_length=MAX_PROMPT_CHARS)
    code: str = Field(default="", max_length=MAX_CODE_CHARS)
    extra_params: Dict[str, str] = {}

class ResumeRequest(BaseModel):
    session_id: int
    new_agent_ids: List[str]
    model: str = Field(default="gemini-2.5-flash")

class DownloadZipRequest(BaseModel):
    files: List[Dict[str, str]]  # [{"path": ..., "content": ...}]

# ─────────────────────────────────────────
# Yardımcılar
# ─────────────────────────────────────────
def _get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_schema(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_prompt TEXT,
            code TEXT,
            teams_data TEXT,
            dependencies_md TEXT,
            codemap_md TEXT,
            context_summary_md TEXT
        )
    """)
    # Migrate older DBs that lack the new columns
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(sessions)")}
    for col, ctype in [
        ("dependencies_md", "TEXT"),
        ("codemap_md", "TEXT"),
        ("context_summary_md", "TEXT")
    ]:
        if col not in existing:
            cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col} {ctype}")

def save_analysis_session(
    user_prompt: str,
    code: str,
    teams_data: list,
    dependencies_md: str = "",
    codemap_md: str = "",
    context_summary_md: str = "",
):
    try:
        conn = _get_db()
        cursor = conn.cursor()
        _ensure_schema(cursor)
        cursor.execute(
            """INSERT INTO sessions
               (user_prompt, code, teams_data, dependencies_md, codemap_md, context_summary_md)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_prompt, code, json.dumps(teams_data, ensure_ascii=False),
             dependencies_md, codemap_md, context_summary_md),
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    except Exception as e:
        print("Veritabanı kayıt hatası:", e)
        return None

def update_analysis_session_teams(session_id: int, new_teams_data: list, context_summary_md: str = ""):
    try:
        conn = _get_db()
        cursor = conn.cursor()
        if context_summary_md:
            cursor.execute(
                "UPDATE sessions SET teams_data = ?, context_summary_md = ? WHERE id = ?",
                (json.dumps(new_teams_data, ensure_ascii=False), context_summary_md, session_id)
            )
        else:
            cursor.execute(
                "UPDATE sessions SET teams_data = ? WHERE id = ?",
                (json.dumps(new_teams_data, ensure_ascii=False), session_id)
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Veritabanı güncelleme hatası:", e)


# ─────────────────────────────────────────
# Endpoint'ler
# ─────────────────────────────────────────
@app.get("/")
def read_root():
    return {"status": "success", "message": "AI Judge Backend Hazır."}


@app.get("/sessions")
def list_sessions():
    """Geçmiş analiz oturumlarının özetini döndürür (en yeni önce)."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        _ensure_schema(cursor)
        rows = cursor.execute(
            "SELECT id, timestamp, user_prompt FROM sessions ORDER BY id DESC LIMIT 50"
        ).fetchall()
        conn.close()
        sessions = [
            {"id": r["id"], "timestamp": r["timestamp"],
             "user_prompt": (r["user_prompt"] or "")[:120]}
            for r in rows
        ]
        return {"status": "success", "sessions": sessions}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/sessions/{session_id}")
def get_session(session_id: int):
    """Belirli bir oturumun tüm verilerini döndürür."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        _ensure_schema(cursor)
        row = cursor.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        conn.close()
        if not row:
            return {"status": "error", "message": "Oturum bulunamadı."}
        return {
            "status": "success",
            "session": {
                "id":             row["id"],
                "timestamp":      row["timestamp"],
                "user_prompt":    row["user_prompt"] or "",
                "teams":          json.loads(row["teams_data"] or "[]"),
                "dependencies_md": row["dependencies_md"] or "",
                "codemap_md":     row["codemap_md"] or "",
                "context_summary_md": row["context_summary_md"] or "",
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}




@app.get("/sessions/{session_id}/report")
async def download_report(session_id: int):
    """
    Geçmiş bir oturumun raporunu Markdown olarak indirir.
    """
    try:
        conn = _get_db()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        conn.close()

        if not row:
            return Response(content="Oturum bulunamadı.", status_code=404)

        teams_data = json.loads(row["teams_data"] or "[]")
        user_prompt = row["user_prompt"] or "İsimsiz Analiz"
        timestamp = row["timestamp"] or ""

        report_md = f"# ⚖️ AI Judge Değerlendirme Raporu\n\n"
        report_md += f"**Tarih:** {timestamp}\n"
        report_md += f"**Talimat:** {user_prompt}\n\n"
        report_md += "---\n\n"

        if row["dependencies_md"]:
            report_md += f"## 📦 Proje Bağımlılıkları\n\n{row['dependencies_md']}\n\n---\n"
        if row["codemap_md"]:
            report_md += f"## 🗺️ Kod Haritası\n\n{row['codemap_md']}\n\n---\n"

        for team in teams_data:
            report_md += f"## 👥 {team.get('name', 'Takım')}\n"
            report_md += f"**Odak Alanı:** {team.get('focus_area', '')}\n\n"
            
            if team.get("final_synthesis"):
                report_md += "### 🏁 Karar / Sentez\n"
                report_md += f"{team['final_synthesis']}\n\n"
            
            if team.get("maker_bot_brief"):
                 report_md += "### 📋 Maker Bot Talimatları\n"
                 report_md += f"{team['maker_bot_brief']}\n\n"

            report_md += "### 📝 Ajan Raporları\n"
            reports = team.get("reports", {})
            for aid, r in reports.items():
                report_md += f"#### 🤖 {aid}\n{r}\n\n"
            
            report_md += "---\n\n"

        filename = f"AI_Judge_Report_{session_id}.md"
        return Response(
            content=report_md,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return Response(content=f"Rapor oluşturma hatası: {str(e)}", status_code=500)


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
    try:
        all_personas = get_all_personas()
        # Dinamik model— frontend'den gelen model adını kullan
        await asyncio.to_thread(agents.set_model, request.model)

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
        async def run_agent_staggered(agent_id, code, focus, feedback, codemap_ctx, deps_ctx, delay, ctx_summary):
            if delay > 0:
                await asyncio.sleep(delay)
            return await asyncio.to_thread(
                agents.run_agent,
                agent_id, code, focus, feedback, codemap_ctx, deps_ctx, ctx_summary
            )

        team_results = []
        global_context_summary = ""
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
                        global_context_summary
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

            # Update the global context summary after the team finishes
            latest_events = f"Takım: {team_name}\nKarar/Sentez: {iteration_history[-1]['consensus_result'].get('synthesis', '')}"
            global_context_summary = await asyncio.to_thread(
                agents.run_context_summarizer,
                global_context_summary, request.user_prompt, latest_events
            )

        # ── Adım 6: Orkestratör — Maker Bot talimatları ───────────────
        for tr in team_results:
            tr["maker_bot_brief"] = await asyncio.to_thread(
                agents.run_orchestrator_summary,
                tr["name"], tr["focus_area"], tr["reports"], tr.get("final_synthesis", ""),
            )

        session_id = save_analysis_session(
            request.user_prompt, request.code, team_results,
            dependencies_md=dependencies_md, codemap_md=codemap_md,
            context_summary_md=global_context_summary
        )
        return {
            "status": "success",
            "session_id": session_id,
            "teams": team_results,
            "dependencies_md": dependencies_md,
            "codemap_md": codemap_md,
            "context_summary_md": global_context_summary
        }
    except QuotaExceededError as qe:
        return {"status": "error", "message": str(qe)}
    except Exception as e:
        return {"status": "error", "message": f"Sistem hatası: {str(e)}"}


@app.post("/analyze/resume")
async def resume_analysis(request: ResumeRequest):
    """
    Kullanıcının önerilen ajanları takıma dahil edip mevcut oturuma eklemesini sağlar.
    Mevcut ajanlar tekrar çalıştırılmaz (token tasarrufu).
    """
    # 0. Dinamik model
    await asyncio.to_thread(agents.set_model, request.model)

    # 1. Oturumu getir
    conn = _get_db()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM sessions WHERE id = ?", (request.session_id,)).fetchone()
    conn.close()

    if not row:
        return {"status": "error", "message": "Oturum bulunamadı."}

    existing_teams = json.loads(row["teams_data"] or "[]")
    code = row["code"] or ""
    deps_md = row["dependencies_md"] or ""
    codemap_md = row["codemap_md"] or ""
    context_summary_md = row["context_summary_md"] or ""

    # Zaten çalışmış olan ajanları bul
    already_run = set()
    for t in existing_teams:
        if "reports" in t:
            already_run.update(t["reports"].keys())
        elif "iterations" in t and t["iterations"]:
            already_run.update(t["iterations"][-1]["reports"].keys())

    # Sadece yeni ajanları filtrele
    new_agents = [aid for aid in request.new_agent_ids if aid not in already_run]
    
    if not new_agents:
        return {
            "status": "success",
            "teams": existing_teams,
            "dependencies_md": deps_md,
            "codemap_md": codemap_md,
            "context_summary_md": context_summary_md,
        }

    # 2. Yeni ajanları yeni bir takımda topla
    team_name = "Ek Katılımcılar (Önerilenler)"
    focus_area = "Çapraz Sorgu ve Yeni Perspektifler"
    
    async def run_agent_staggered(agent_id, delay):
        if delay > 0:
            await asyncio.sleep(delay)
        return await asyncio.to_thread(
            agents.run_agent,
            agent_id, code, focus_area, "", codemap_md[:600], deps_md[:600], context_summary_md
        )

    tasks = [run_agent_staggered(aid, idx * STAGGER_DELAY_SECONDS) for idx, aid in enumerate(new_agents)]
    reports = await asyncio.gather(*tasks)
    member_reports = dict(zip(new_agents, reports))

    consensus_result = (
        await asyncio.to_thread(agents.run_consensus_checker, team_name, member_reports, focus_area)
        if len(new_agents) > 1
        else {"consensus_reached": True, "feedback": "", "synthesis": "Tek kişilik takım."}
    )

    new_team = {
        "name": team_name,
        "focus_area": focus_area,
        "members": new_agents,
        "iterations": [{
            "iteration": 1,
            "reports": member_reports,
            "consensus_result": consensus_result
        }],
        "reports": member_reports,
        "final_synthesis": consensus_result.get("synthesis", ""),
        "maker_bot_brief": ""
    }

    # 3. Orkestratör — Maker Bot talimatları
    new_team["maker_bot_brief"] = await asyncio.to_thread(
        agents.run_orchestrator_summary,
        new_team["name"], new_team["focus_area"], new_team["reports"], new_team.get("final_synthesis", ""),
    )

    # 4. Yeni takımı listeye ekle ve DB'yi güncelle
    existing_teams.append(new_team)

    # Update the global context summary
    latest_events = f"Yeni Takım Eklendi: {team_name}\nKarar/Sentez: {consensus_result.get('synthesis', '')}"
    context_summary_md = await asyncio.to_thread(
        agents.run_context_summarizer,
        context_summary_md, "Yeni ajanlarla analiz devam ediyor", latest_events
    )

    update_analysis_session_teams(request.session_id, existing_teams, context_summary_md)

    return {
        "status": "success",
        "teams": existing_teams,
        "dependencies_md": deps_md,
        "codemap_md": codemap_md,
        "context_summary_md": context_summary_md,
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


@app.post("/generate")
async def generate_code(request: GenerateRequest):
    """Mode bazlı kod üretici: prototipleme, versiyon güncelleme, dil değişikliği, sıfırdan üretme."""
    if not request.user_prompt and not request.code:
        return {"status": "error", "message": "En az bir talimat veya kod girilmelidir."}
    result = await asyncio.to_thread(
        agents.run_code_generator,
        request.mode, request.user_prompt, request.code, dict(request.extra_params),
    )
    return {"status": "success", "mode": request.mode, "result": result}


@app.post("/generate/download-zip")
async def download_generated_zip(request: DownloadZipRequest):
    """Verilen dosya listesinden ZIP oluşturur ve indirir."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in request.files:
            path = f.get("path", "file.txt").lstrip("/")
            content = f.get("content", "")
            zf.writestr(path, content)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="generated_project.zip"'},
    )