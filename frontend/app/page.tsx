"use client";
import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import HistoryDrawer from "./components/HistoryDrawer";
import FileTreeViewer, { parseGeneratedFiles, GenFile } from "./components/FileTreeViewer";

const TeamCard = ({ team, personas, getBoardColor }: any) => {
  const [currentIterIdx, setCurrentIterIdx] = useState(
    team.iterations ? team.iterations.length - 1 : 0
  );

  const iterations = team.iterations || [];
  const currentIter = iterations[currentIterIdx] || { reports: team.reports };
  const reportsToDisplay = currentIter.reports || team.reports;

  return (
    <div className="mb-10 bg-slate-100/50 p-6 rounded-3xl border border-slate-200">
      <div className="mb-6 border-b border-slate-300 pb-4">
        <h2 className="text-2xl font-extrabold text-slate-800 mb-2 flex items-center gap-2">
          <span className="text-3xl">👥</span> {team.name}
        </h2>
        <div className="inline-block bg-white text-indigo-700 text-base font-medium px-4 py-2 rounded-xl border border-indigo-200 shadow-sm">
          🎯 <span className="font-bold">Odak Alanı:</span> {team.focus_area}
        </div>

        {iterations.length > 0 && (
          <div className="mt-4 flex items-center gap-4 bg-white p-2 rounded-xl inline-flex border border-slate-200 shadow-sm">
            <button
              onClick={() => setCurrentIterIdx(Math.max(0, currentIterIdx - 1))}
              disabled={currentIterIdx === 0}
              className="px-3 py-1 bg-slate-100 rounded-lg hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed font-medium text-sm transition-all text-slate-700"
            >
              ◀ Önceki Tur
            </button>
            <span className="font-bold text-slate-700 text-sm">
              İterasyon {currentIterIdx + 1} / {iterations.length}
            </span>
            <button
              onClick={() => setCurrentIterIdx(Math.min(iterations.length - 1, currentIterIdx + 1))}
              disabled={currentIterIdx === iterations.length - 1}
              className="px-3 py-1 bg-slate-100 rounded-lg hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed font-medium text-sm transition-all text-slate-700"
            >
              Sonraki Tur ▶
            </button>
          </div>
        )}
      </div>

      {team.final_synthesis && team.final_synthesis !== "Tek kişilik takım." && currentIterIdx === iterations.length - 1 && (
        <div className="mb-4 p-5 bg-emerald-50 border border-emerald-200 rounded-xl shadow-sm">
          <h3 className="text-lg font-bold text-emerald-800 mb-1 flex items-center gap-2">
            <span>🤝</span> Takım Uzlaşı Özeti
          </h3>
          <p className="text-base text-emerald-700 leading-relaxed">{team.final_synthesis}</p>
        </div>
      )}

      {team.maker_bot_brief && (
        <details className="mb-4 rounded-xl overflow-hidden" style={{ border: '1.5px solid #fef3c7' }}>
          <summary className="px-5 py-3 cursor-pointer font-semibold text-sm select-none flex items-center gap-2" style={{ background: '#fffbeb', color: '#d97706' }}>
            📋 Orkestratör Briefing
          </summary>
          <div className="px-5 py-4 prose prose-sm max-w-none prose-headings:text-amber-800" style={{ background: '#fdf8f6' }}>
            <ReactMarkdown>{team.maker_bot_brief}</ReactMarkdown>
          </div>
        </details>
      )}

      {currentIter.consensus_result && !currentIter.consensus_result.consensus_reached && (
        <div className="mb-6 p-5 bg-amber-50 border border-amber-200 rounded-xl shadow-sm">
          <h3 className="text-lg font-bold text-amber-800 mb-1 flex items-center gap-2">
            <span>⚠️</span> Moderatör Geri Bildirimi (Çelişki Tespit Edildi)
          </h3>
          <p className="text-base text-amber-700 leading-relaxed">{currentIter.consensus_result.feedback}</p>
        </div>
      )}

      <div className="flex flex-col gap-6">
        {Object.entries(reportsToDisplay).map(([agentId, reportContent]: [string, any]) => {
          const meta = personas[agentId];
          if (!meta) return null;
          const colors = getBoardColor(meta.board);

          return (
            <div key={agentId} className="bg-white p-8 rounded-2xl shadow-sm border-l-8 hover:shadow-md transition-shadow" style={{ borderLeftColor: colors.border }}>
              <div className="flex items-center gap-3 mb-6 border-b pb-4">
                <span className="text-3xl">{meta.icon}</span>
                <div>
                  <h3 className="text-xl font-bold" style={{ color: colors.text }}>{meta.display_name}</h3>
                  <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">{meta.role}</p>
                </div>
              </div>
              <div className="prose prose-base prose-slate max-w-none prose-headings:text-slate-800 prose-a:text-blue-600">
                <ReactMarkdown>{reportContent}</ReactMarkdown>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};


export default function Home() {
  const [mounted, setMounted] = useState(false);
  const [inputCode, setInputCode] = useState("");
  const [userPrompt, setUserPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [makerBotLoading, setMakerBotLoading] = useState(false);
  const [makerBotRevisions, setMakerBotRevisions] = useState<any[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [personas, setPersonas] = useState<Record<string, any>>({});
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [teamReports, setTeamReports] = useState<any[]>([]);
  const [dependenciesMd, setDependenciesMd] = useState<string>("");
  const [codemapMd, setCodemapMd] = useState<string>("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [currentSession, setCurrentSession] = useState<any>(null);
  // Mode
  const [mode, setMode] = useState<"inceleme" | "prototipleme" | "versiyon_guncelleme" | "dil_degisikligi" | "sifirdan_uretme">("inceleme");
  const [extraParams, setExtraParams] = useState<Record<string, string>>({});
  const [generatedFiles, setGeneratedFiles] = useState<GenFile[]>([]);
  const [generatedRaw, setGeneratedRaw] = useState<string>("");
  const [generating, setGenerating] = useState(false);

  const MAX_CODE_CHARS = 100000;
  const MAX_PROMPT_CHARS = 1000;

  useEffect(() => {
    setMounted(true);
    // Persona listesini backend'den çek
    fetch("http://localhost:8001/personas")
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          setPersonas(data.personas);
          // Varsayılan olarak ilk iki ajanı seçelim (Socrates ve Alan Turing varsa)
          const defaultAgents = ["socrates", "alan_turing"].filter(id => data.personas[id]);
          setSelectedAgents(defaultAgents.length > 0 ? defaultAgents : Object.keys(data.personas).slice(0, 2));
        }
      })
      .catch((err) => console.error("Persona yükleme hatası:", err));
  }, []);

  const handleNewChat = () => {
    setInputCode("");
    setUserPrompt("");
    setTeamReports([]);
    setDependenciesMd("");
    setCodemapMd("");
    setMakerBotRevisions([]);
    setGeneratedFiles([]);
    setGeneratedRaw("");
    setCurrentSession(null);
    setUploadedFiles([]);
    setMode("inceleme");
    // Dosya input'larını da temizlemek için bir referans kullanılabilir ama şimdilik state yeterli.
  };

  const handleAnalyze = async () => {
    if (!inputCode || (!userPrompt.trim() && selectedAgents.length === 0)) return;
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8001/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code: inputCode, user_prompt: userPrompt, agent_ids: selectedAgents }),
      });

      const data = await response.json();
      if (data.status === "success") {
        setTeamReports(data.teams);
        setDependenciesMd(data.dependencies_md || "");
        setCodemapMd(data.codemap_md || "");
        // Drawer için mevcut oturumu oluştur (DB'ye kaydedilince ID gelecek, şimşilik local)
        setCurrentSession({
          id: data.session_id || Date.now(),
          timestamp: new Date().toISOString(),
          user_prompt: userPrompt,
          teams: data.teams,
          dependencies_md: data.dependencies_md || "",
          codemap_md: data.codemap_md || "",
        });
        setDrawerOpen(true);
        const allChosenAgents = data.teams.flatMap((t: any) => Object.keys(t.reports));
        if (allChosenAgents.length > 0) {
          setSelectedAgents(allChosenAgents);
        }
      } else {
        alert(data.message || "Bir hata oluştu.");
      }
    } catch (error) {
      console.error("API Hatası:", error);
      alert("Bağlantı hatası! Backend'in 8001 portunda çalıştığına emin ol.");
    }
    setLoading(false);
  };

  const handleResume = async () => {
    if (!currentSession || !currentSession.id || selectedAgents.length === 0) return;
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8001/analyze/resume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: currentSession.id, new_agent_ids: selectedAgents }),
      });

      const data = await response.json();
      if (data.status === "success") {
        setTeamReports(data.teams);
        setDependenciesMd(data.dependencies_md || "");
        setCodemapMd(data.codemap_md || "");
        setCurrentSession({
          ...currentSession,
          teams: data.teams,
          dependencies_md: data.dependencies_md || "",
          codemap_md: data.codemap_md || "",
        });
        setDrawerOpen(true);
      } else {
        alert(data.message || "Mevcut analize eklenirken hata oluştu.");
      }
    } catch (error) {
      console.error("API Hatası:", error);
      alert("Bağlantı hatası! Backend'in 8001 portunda çalıştığına emin ol.");
    }
    setLoading(false);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    formData.append("file", files[0]);

    try {
      const res = await fetch("http://localhost:8001/upload-file", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.status === "success") {
        setInputCode(prev => (prev ? prev + "\n\n" : "") + data.content);
        const label = data.is_zip
          ? `${data.filename} (${data.file_count} dosya)`
          : data.filename;
        setUploadedFiles(prev => [...prev, label]);
        if (data.truncated) {
          alert(`⚠️ "${data.filename}" içeriği ${MAX_CODE_CHARS.toLocaleString()} karakter limitinde kesildi.`);
        }
      } else {
        alert(data.message || "Dosya yüklenemedi.");
      }
    } catch {
      alert("Dosya yükleme bağlantı hatası!");
    }
    // Input'u sıfırla ki aynı dosya tekrar seçilebilsin
    e.target.value = "";
  };

  const handleRemoveFile = (index: number) => {
    setUploadedFiles(prev => {
      const newFiles = prev.filter((_, i) => i !== index);
      if (newFiles.length === 0) {
        setInputCode("");
      }
      return newFiles;
    });
  };

  const handleMakerBot = async () => {
    if (teamReports.length === 0) return;
    setMakerBotLoading(true);
    setMakerBotRevisions([]);
    try {
      const res = await fetch("http://localhost:8001/maker-bot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_prompt: userPrompt, teams: teamReports }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setMakerBotRevisions(data.team_revisions);
      } else {
        alert(data.message || "Maker Bot hata verdi.");
      }
    } catch {
      alert("Maker Bot bağlantı hatası!");
    }
    setMakerBotLoading(false);
  };

  const MODES = [
    { id: "inceleme", icon: "🔍", label: "İnceleme", desc: "Kodu uzman kurullarla analiz et" },
    { id: "prototipleme", icon: "🚀", label: "Prototipleme", desc: "Fikrinden hızlıca prototip üret" },
    { id: "versiyon_guncelleme", icon: "⬆️", label: "Versiyon Güncelleme", desc: "Kodu yeni versiyona taşı" },
    { id: "dil_degisikligi", icon: "🔄", label: "Dil Değişikliği", desc: "Farklı bir dile migrate et" },
    { id: "sifirdan_uretme", icon: "✨", label: "Sıfırdan Üretme", desc: "Projeni sıfırdan inşa et" },
  ] as const;

  const handleGenerate = async () => {
    if (!userPrompt.trim() && !inputCode.trim()) return;
    setGenerating(true);
    setGeneratedFiles([]);
    setGeneratedRaw("");
    try {
      const res = await fetch("http://localhost:8001/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, user_prompt: userPrompt, code: inputCode, extra_params: extraParams }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setGeneratedRaw(data.result);
        setGeneratedFiles(parseGeneratedFiles(data.result));
      } else {
        alert(data.message || "Üretim sırasında hata oluştu.");
      }
    } catch { alert("Bağlantı hatası!"); }
    setGenerating(false);
  };

  const downloadAnalysisReport = () => {
    const parts: string[] = ["# 🏛️ Curator AI Değerlendirme Raporu\n"];
    if (dependenciesMd) parts.push(`## 📦 Proje Bağımlılıkları\n\n${dependenciesMd}\n\n---\n`);
    if (codemapMd) parts.push(`## 🗺️ Kod Haritası\n\n${codemapMd}\n\n---\n`);
    teamReports.forEach((team: any) => {
      parts.push(`\n# 👥 ${team.name}\n**Odak:** ${team.focus_area}\n`);
      if (team.final_synthesis) parts.push(`**Uzlaşı:** ${team.final_synthesis}\n`);
      if (team.maker_bot_brief) parts.push(`\n## 📋 Orkestratör Briefing\n${team.maker_bot_brief}\n`);
      Object.entries(team.reports || {}).forEach(([aid, report]) =>
        parts.push(`\n### ${aid}\n${report}\n`)
      );
    });
    makerBotRevisions.forEach((rev: any) => {
      parts.push(`\n## 🤖 Sentez Merkezi — ${rev.team_name}\n### Briefing\n${rev.brief}\n### Revizyon\n${rev.revision}\n`);
    });
    const blob = new Blob([parts.join("\n")], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "curator_ai_rapor.md"; a.click();
    URL.revokeObjectURL(url);
  };

  const getBoardColor = (boardName: string) => {
    if (boardName === "historical_thinkers") return { border: "#f59e0b", text: "#b45309" }; // amber
    if (boardName === "technical_experts") return { border: "#475569", text: "#334155" }; // slate
    return { border: "#10b981", text: "#047857" }; // emerald
  };

  return (
    <div className="min-h-screen text-slate-900 flex font-sans" style={{ background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%)' }}>
      {/* Geçmiş Drawer */}
      <HistoryDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        currentSession={currentSession}
      />

      {/* Sol Sidebar */}
      <aside className="w-16 flex flex-col items-center py-6 gap-6 flex-shrink-0 sticky top-0 h-screen z-50" style={{ background: '#0f172a', borderRight: '1px solid #1e293b' }}>
        {/* Logo — düz metin, tıklanabilir DEĞİL */}
        <div className="flex flex-col items-center select-none" title="Logos Arena">
          <span className="text-4xl leading-none">🏛️</span>
          <span className="text-[10px] font-bold mt-2" style={{ color: '#94a3b8', letterSpacing: '0.1em' }}>LOGOS</span>
        </div>

        <div className="w-8 h-px" style={{ background: '#1e293b' }} />

        <button
          onClick={() => setDrawerOpen(true)}
          className="group relative p-3 rounded-2xl transition-all"
          style={{ background: '#1e293b' }}
          onMouseEnter={e => (e.currentTarget.style.background = '#334155')}
          onMouseLeave={e => (e.currentTarget.style.background = '#1e293b')}
        >
          <span className="text-xl">📂</span>
          <span className="absolute left-full ml-3 px-3 py-2 text-white text-sm font-bold rounded-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-[100] shadow-2xl" style={{ background: '#334155', border: '1px solid #475569' }}>Geçmiş Analizler</span>
        </button>

        <button
          onClick={handleNewChat}
          className="group relative p-3 rounded-2xl transition-all"
          style={{ background: '#0f766e' }}
          onMouseEnter={e => (e.currentTarget.style.background = '#14b8a6')}
          onMouseLeave={e => (e.currentTarget.style.background = '#0f766e')}
        >
          <span className="text-xl">✨</span>
          <span className="absolute left-full ml-3 px-3 py-2 text-white text-sm font-bold rounded-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-[100] shadow-2xl" style={{ background: '#0f766e', border: '1px solid #14b8a6' }}>Yeni Sohbet</span>
        </button>

        <div className="mt-auto flex flex-col items-center gap-4 pb-4">
          <button
            onClick={() => setAboutOpen(true)}
            className="group relative p-3 rounded-2xl transition-all"
            style={{ background: '#1e293b' }}
            onMouseEnter={e => (e.currentTarget.style.background = '#334155')}
            onMouseLeave={e => (e.currentTarget.style.background = '#1e293b')}
          >
            <span className="text-xl">ℹ️</span>
            <span className="absolute left-full ml-3 px-3 py-2 text-white text-sm font-bold rounded-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-[100] shadow-2xl" style={{ background: '#334155', border: '1px solid #475569' }}>Hakkında</span>
          </button>

          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold" style={{ background: '#1e293b', color: '#94a3b8' }}>AI</div>
        </div>
      </aside>

      {/* Ana İçerik Alanı */}
      <div className="flex-1 p-8 overflow-x-hidden">
        <header className="mb-8 pb-5" style={{ borderBottom: '2px solid #cbd5e1' }}>
          <h1 className="text-5xl font-extrabold tracking-tight" style={{ color: '#0f172a' }}>Curator <span style={{ background: 'linear-gradient(90deg,#0f766e,#d97706)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>AI</span></h1>
          <p className="mt-2 text-xl" style={{ color: '#475569' }}>Projenizi Logos Arena'ya yükleyin, uzman kurullarımız sentezleyip raporlasın.</p>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* SOL PANEL: Girdi Alanı */}
          <div className="flex flex-col gap-5 bg-white p-7 rounded-3xl shadow-md" style={{ border: '1.5px solid #cbd5e1' }}>
            {/* Mode Seçici */}
            <div>
              <h2 className="text-2xl font-extrabold mb-1" style={{ color: '#0f172a' }}>Ne yapmak istiyorsunuz?</h2>
              <p className="text-sm mb-4" style={{ color: '#64748b' }}>Aşağıdan bir yetenek seçin, ekran buna göre düzenlensin.</p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {MODES.map(m => (
                  <button key={m.id} onClick={() => { setMode(m.id as any); setGeneratedFiles([]); setGeneratedRaw(""); }}
                    className="flex flex-col items-start p-3 rounded-2xl text-left transition-all"
                    style={mode === m.id
                      ? { background: '#f0fdfa', border: '2px solid #0f766e', boxShadow: '0 2px 12px #0f766e30' }
                      : { background: '#f8fafc', border: '1.5px solid #cbd5e1' }}>
                    <span className="text-xl mb-1">{m.icon}</span>
                    <span className="text-sm font-bold" style={{ color: mode === m.id ? '#0f766e' : '#334155' }}>{m.label}</span>
                    <span className="text-xs mt-0.5 leading-tight" style={{ color: '#64748b' }}>{m.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <hr style={{ borderColor: '#cbd5e1' }} />

            {/* Mode'a Özel Ek Alanlar */}
            {mode === "versiyon_guncelleme" && (
              <div>
                <h3 className="text-sm font-bold uppercase tracking-widest mb-2" style={{ color: '#0f766e' }}>Hedef Versiyon / Framework</h3>
                <input className="w-full p-4 rounded-2xl text-base focus:outline-none" style={{ border: '1.5px solid #94a3b8', background: '#f8fafc', color: '#0f172a' }}
                  placeholder="Örn: React 18, Next.js 15, Python 3.12..."
                  value={extraParams.target_version || ""}
                  onChange={e => setExtraParams(p => ({ ...p, target_version: e.target.value }))} />
              </div>
            )}
            {mode === "dil_degisikligi" && (
              <div className="flex gap-3">
                <div className="flex-1">
                  <h3 className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: '#0f766e' }}>Kaynak Dil</h3>
                  <input className="w-full p-3 rounded-2xl text-sm focus:outline-none" style={{ border: '1.5px solid #94a3b8', background: '#f8fafc', color: '#0f172a' }}
                    placeholder="Örn: Python, JavaScript..."
                    value={extraParams.source_lang || ""}
                    onChange={e => setExtraParams(p => ({ ...p, source_lang: e.target.value }))} />
                </div>
                <div className="flex-1">
                  <h3 className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: '#0f766e' }}>Hedef Dil</h3>
                  <input className="w-full p-3 rounded-2xl text-sm focus:outline-none" style={{ border: '1.5px solid #94a3b8', background: '#f8fafc', color: '#0f172a' }}
                    placeholder="Örn: Go, TypeScript..."
                    value={extraParams.target_lang || ""}
                    onChange={e => setExtraParams(p => ({ ...p, target_lang: e.target.value }))} />
                </div>
              </div>
            )}
            {mode === "sifirdan_uretme" && (
              <div>
                <h3 className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: '#0f766e' }}>Teknoloji Yığını (Opsiyonel)</h3>
                <input className="w-full p-3 rounded-2xl text-sm focus:outline-none" style={{ border: '1.5px solid #94a3b8', background: '#f8fafc', color: '#0f172a' }}
                  placeholder="Örn: Next.js + FastAPI + PostgreSQL..."
                  value={extraParams.tech_stack || ""}
                  onChange={e => setExtraParams(p => ({ ...p, tech_stack: e.target.value }))} />
              </div>
            )}

            {/* Ajan Seçimi — sadece İnceleme modunda */}
            {mode === "inceleme" && (
              <div>
                <h3 className="text-lg font-bold mb-3 uppercase tracking-widest" style={{ color: '#d97706', fontSize: '0.85rem' }}>Komite Üyelerini Seçin</h3>
                <div className="flex flex-wrap gap-2 overflow-visible">
                  {Object.entries(personas).map(([id, meta]) => (
                    <label key={id} className="group relative flex items-center gap-2 cursor-pointer transition-all" style={selectedAgents.includes(id)
                      ? { background: '#fffbeb', border: '2px solid #d97706', borderRadius: '12px', padding: '6px 12px', boxShadow: '0 2px 8px #d9770620' }
                      : { background: '#f8fafc', border: '1.5px solid #cbd5e1', borderRadius: '12px', padding: '6px 12px' }}>
                      <input type="checkbox" className="hidden" checked={selectedAgents.includes(id)}
                        onChange={(e) => {
                          if (e.target.checked) setSelectedAgents([...selectedAgents, id]);
                          else setSelectedAgents(selectedAgents.filter(a => a !== id));
                        }}
                      />
                      <span className="text-lg">{meta.icon}</span>
                      <span className="text-sm font-semibold" style={{ color: selectedAgents.includes(id) ? '#b45309' : '#334155' }}>{meta.display_name}</span>
                      {/* Tooltip — aşağıya açılır, clipping yok */}
                      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-56 p-3 bg-slate-800 text-white text-xs rounded-xl shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-[100] whitespace-normal">
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
                        <p className="font-bold text-amber-300 mb-1">{meta.role}</p>
                        <p className="text-slate-300 leading-relaxed">
                          <span className="font-semibold text-slate-400">Uzmanlık:</span> {meta.expertise?.join(', ')}
                        </p>
                      </div>
                    </label>
                  ))}
                  {Object.keys(personas).length === 0 && (
                    <div className="text-sm text-slate-400 animate-pulse">Kurul üyeleri salona davet ediliyor...</div>
                  )}
                </div>
              </div>
            )}

            {/* Dosya Yükleme */}
            <div>
              <h3 className="text-sm font-bold mb-2 uppercase tracking-widest" style={{ color: '#0f766e', fontSize: '0.75rem' }}>Dosya Yükle <span style={{ color: '#94a3b8', fontWeight: 400 }}>(Opsiyonel)</span></h3>
              <label className="flex flex-col items-center justify-center w-full h-20 rounded-2xl cursor-pointer transition-all" style={{ border: '2px dashed #94a3b8', background: '#f8fafc' }} onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#f0fdfa'; (e.currentTarget as HTMLElement).style.borderColor = '#0f766e'; }} onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = '#f8fafc'; (e.currentTarget as HTMLElement).style.borderColor = '#94a3b8'; }}>
                <div className="flex flex-col items-center justify-center">
                  <span className="text-2xl mb-1">📂</span>
                  <span className="text-xs text-slate-500 text-center px-2">
                    ZIP (tam proje), .py .ts .tsx .js .jsx .java .go .rs .cpp .c .php .rb .swift .kt .dart · .json .yaml .toml · .html .css .svg .vue .svelte · .sql .sh .bat .md .txt ve daha fazlası
                  </span>
                </div>
                <input type="file" className="hidden"
                  accept=".zip,.py,.ts,.tsx,.js,.jsx,.txt,.md,.json,.css,.html,.yaml,.yml,.env,.toml,.ini,.c,.cpp,.h,.java,.go,.rs,.rb,.php,.swift,.kt,.dart,.sql,.sh,.bat,.ps1,.xml,.svg,.vue,.svelte,.graphql,.proto"
                  onChange={handleFileUpload} />
              </label>
              {uploadedFiles.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {uploadedFiles.map((f, i) => (
                    <span key={i} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium flex items-center gap-1">
                      📄 {f}
                      <button
                        onClick={() => handleRemoveFile(i)}
                        className="hover:bg-blue-200 rounded-full w-4 h-4 flex items-center justify-center transition-colors font-bold text-[10px]"
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Karar Verici Prompt Alanı */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-bold uppercase tracking-widest" style={{ color: '#d97706', fontSize: '0.75rem' }}>Orkestratör Talimatınız <span style={{ color: '#94a3b8', fontWeight: 400 }}>(Opsiyonel)</span></h3>
                <span className={`text-xs font-mono ${userPrompt.length > MAX_PROMPT_CHARS * 0.85 ? 'text-red-500 font-bold' : 'text-slate-400'}`}>
                  {userPrompt.length}/{MAX_PROMPT_CHARS}
                </span>
              </div>
              <textarea
                className="w-full h-24 p-4 rounded-2xl text-base resize-none focus:outline-none transition-all"
                style={{ border: '1.5px solid #94a3b8', background: '#f8fafc', color: '#0f172a', fontFamily: 'inherit' }}
                placeholder={mode === 'inceleme' ? 'Örn: Sadece frontend odaklı bir değerlendirme istiyorum. Komite tasarıma dikkat etsin.' : 'Örn: Bir React + FastAPI todo uygulaması üret...'}
                maxLength={MAX_PROMPT_CHARS}
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
              />
              <p className="text-xs mt-1.5" style={{ color: '#d97706' }}>Talimat girerseniz, komiteler Orkestratör tarafından otomatik seçilir ve sentez sırasına dizilir.</p>
            </div>

            <div className="relative">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-bold uppercase tracking-widest" style={{ color: '#0f766e', fontSize: '0.75rem' }}>Kod / Konsept</span>
                <span className="text-xs font-mono" style={{ color: inputCode.length > MAX_CODE_CHARS * 0.9 ? '#ef4444' : '#94a3b8' }}>
                  {inputCode.length.toLocaleString()}&nbsp;/&nbsp;{MAX_CODE_CHARS.toLocaleString()}
                </span>
              </div>
              <textarea
                className="w-full h-64 p-4 rounded-2xl font-mono text-sm resize-none focus:outline-none transition-all"
                style={{ border: '1.5px solid #cbd5e1', background: '#ffffff', color: '#0f172a', lineHeight: '1.6' }}
                placeholder="İncelemeye alınacak kodu veya uygulama konseptini buraya yapıştırın..."
                maxLength={MAX_CODE_CHARS}
                value={inputCode}
                onChange={(e) => setInputCode(e.target.value)}
              />
            </div>
            {mode === "inceleme" ? (
              <div className="flex gap-4 mt-1">
                <button
                  onClick={handleAnalyze}
                  disabled={!mounted || loading || !inputCode.trim() || (!userPrompt.trim() && selectedAgents.length === 0)}
                  suppressHydrationWarning={true}
                  className="flex-1 text-white font-bold py-4 px-6 rounded-2xl text-base transition-all flex justify-center items-center gap-2 disabled:opacity-50"
                  style={{ background: loading ? '#0d9488' : 'linear-gradient(135deg,#0f766e,#d97706)', boxShadow: '0 4px 20px #0f766e40' }}
                >
                  {loading ? <span className="animate-pulse">⏳ Çalışıyor...</span> : <span>⚡ Yeni Değerlendirme Başlat</span>}
                </button>
                {currentSession && currentSession.id && (
                  <button
                    onClick={handleResume}
                    disabled={!mounted || loading || selectedAgents.length === 0}
                    className="flex-1 text-teal-700 font-bold py-4 px-6 rounded-2xl text-base transition-all flex justify-center items-center gap-2 disabled:opacity-50 bg-teal-50 border-2 border-teal-200 hover:bg-teal-100 hover:border-teal-300"
                  >
                    {loading ? "⏳ Ekleniyor..." : "➕ Mevcut Analize Ekle"}
                  </button>
                )}
              </div>
            ) : (
              <button
                onClick={handleGenerate}
                disabled={!mounted || generating || (!userPrompt.trim() && !inputCode.trim())}
                suppressHydrationWarning={true}
                className="mt-1 w-full text-white font-bold py-4 px-6 rounded-2xl text-base transition-all flex justify-center items-center gap-2 disabled:opacity-50"
                style={{ background: generating ? '#0d9488' : 'linear-gradient(135deg,#0f766e,#d97706)', boxShadow: '0 4px 20px #0f766e40' }}
              >
                {generating ? <span className="animate-pulse">⏳ Üretiliyor...</span> : <span>✨ {MODES.find(m => m.id === mode)?.label} Başlat</span>}
              </button>
            )}

            {/* Maker Bot Butonu - Sadece analiz tamamlandıktan sonra görünür */}
            {teamReports.length > 0 && (
              <button
                onClick={handleMakerBot}
                disabled={makerBotLoading}
                className="mt-2 w-full bg-gradient-to-r from-amber-600 to-teal-700 text-white font-bold py-3 px-6 rounded-xl hover:from-amber-700 hover:to-teal-800 transition-all disabled:opacity-50 flex justify-center items-center gap-2 shadow-lg"
              >
                {makerBotLoading ? (
                  <span className="animate-pulse">⚙️ Sentez Merkezi Çalışıyor...</span>
                ) : (
                  <span>🤖 Sentez Merkezi: Nihai Revizyon Planı Üret</span>
                )}
              </button>
            )}
          </div>

          {/* SAĞ PANEL */}
          <div className="flex flex-col gap-6 h-[85vh] overflow-y-auto pr-2 pb-12">

            {/* Üretim Modu — FileTreeViewer */}
            {mode !== "inceleme" && (
              <>
                {generating && (
                  <div className="h-48 flex items-center justify-center rounded-3xl text-lg animate-pulse"
                    style={{ border: '2px dashed #94a3b8', background: '#f8fafc', color: '#0f766e' }}>
                    ⚙️ Küratör AI üretiyor, lütfen bekleyin...
                  </div>
                )}
                {!generating && generatedFiles.length > 0 && (
                  <div className="flex flex-col gap-4">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{MODES.find(m => m.id === mode)?.icon}</span>
                      <div>
                        <h2 className="text-xl font-extrabold" style={{ color: '#0f172a' }}>{MODES.find(m => m.id === mode)?.label} Sonucu</h2>
                        <p className="text-sm" style={{ color: '#475569' }}>{generatedFiles.length} dosya üretildi — ZIP ile indirebilirsiniz.</p>
                      </div>
                    </div>
                    <FileTreeViewer files={generatedFiles} />
                  </div>
                )}
                {!generating && generatedFiles.length === 0 && (
                  <div className="h-full flex flex-col items-center justify-center rounded-3xl p-8 text-center" style={{ border: '2px dashed #94a3b8', background: '#f8fafc' }}>
                    <span className="text-5xl mb-4">{MODES.find(m => m.id === mode)?.icon}</span>
                    <p className="text-lg font-bold" style={{ color: '#0f766e' }}>{MODES.find(m => m.id === mode)?.label} sonuçları burada görünecek</p>
                    <p className="text-base mt-2" style={{ color: '#475569' }}>Sol paneli doldurup butona basın.</p>
                  </div>
                )}
              </>
            )}

            {/* İnceleme Modu — Bekleme / Boş Durum */}
            {mode === "inceleme" && teamReports.length === 0 && !loading && (
              <div className="h-full flex flex-col items-center justify-center rounded-3xl p-8 text-center" style={{ border: '2px dashed #94a3b8', background: '#f8fafc' }}>
                <span className="text-5xl mb-4">🏛️</span>
                <p className="text-lg font-bold" style={{ color: '#0f766e' }}>Komite raporları burada görüntülenecek</p>
                <p className="text-base mt-2" style={{ color: '#475569' }}>Sol panelden talimatınızı verin ve değerlendirmeyi başlatın.</p>
              </div>
            )}


            {/* Yükleniyor Ekranı */}
            {loading && (
              <div className="h-full flex items-center justify-center text-blue-500 border-2 border-dashed border-blue-200 rounded-2xl bg-blue-50/50">
                <span className="animate-bounce text-2xl">⏳ Takımlar kuruluyor ve kod inceleniyor...</span>
              </div>
            )}

            {/* İndirme Butonu — Analiz tamamlanınca görünür */}
            {!loading && mode === "inceleme" && teamReports.length > 0 && (
              <div className="flex items-center justify-between px-5 py-3 rounded-2xl" style={{ background: 'linear-gradient(135deg,#eef2ff,#f5f3ff)', border: '1.5px solid #c7d2fe' }}>
                <div>
                  <p className="text-sm font-bold" style={{ color: '#1e1b4b' }}>📊 Analiz Tamamlandı</p>
                  <p className="text-xs" style={{ color: '#6b7280' }}>{teamReports.length} takım · {makerBotRevisions.length > 0 ? "Sentez Merkezi dahil" : "Sentez Merkezi henüz çalışmadı"}</p>
                </div>
                <button
                  onClick={downloadAnalysisReport}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold text-white transition-all"
                  style={{ background: 'linear-gradient(135deg,#0f766e,#d97706)', boxShadow: '0 2px 12px #0f766e40' }}
                >
                  ⬇️ Raporu İndir (.md)
                </button>
              </div>
            )}

            {/* dependencies.md ve codemap.md panelleri */}
            {!loading && (dependenciesMd || codemapMd) && (

              <div className="flex flex-col gap-3 mb-6">
                {dependenciesMd && (
                  <details className="bg-white rounded-2xl border border-emerald-200 shadow-sm overflow-hidden">
                    <summary className="px-5 py-3 cursor-pointer font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 transition-colors flex items-center gap-2 select-none">
                      <span>📦</span> Proje Bağımlılık Raporu (dependencies.md)
                    </summary>
                    <div className="px-5 py-4 prose prose-sm max-w-none prose-headings:text-emerald-800 prose-strong:text-emerald-700">
                      <ReactMarkdown>{dependenciesMd}</ReactMarkdown>
                    </div>
                  </details>
                )}
                {codemapMd && (
                  <details className="bg-white rounded-2xl border border-sky-200 shadow-sm overflow-hidden">
                    <summary className="px-5 py-3 cursor-pointer font-bold text-sky-800 bg-sky-50 hover:bg-sky-100 transition-colors flex items-center gap-2 select-none">
                      <span>🗺️</span> Kod Haritası (codemap.md)
                    </summary>
                    <div className="px-5 py-4 prose prose-sm max-w-none prose-headings:text-sky-800 prose-strong:text-sky-700 prose-table:text-xs">
                      <ReactMarkdown>{codemapMd}</ReactMarkdown>
                    </div>
                  </details>
                )}
              </div>
            )}

            {/* DİNAMİK RAPORLAR (TAKIM BAZLI) */}
            {!loading && teamReports.map((team, tIdx) => (
              <TeamCard key={tIdx} team={team} personas={personas} getBoardColor={getBoardColor} />
            ))}

            {/* MAKER BOT SONUCU (TAKIM BAZLI) */}
            {makerBotRevisions.length > 0 && (
              <div className="mb-10">
                <div className="mb-4 flex items-center gap-3">
                  <span className="text-3xl">🤖</span>
                  <div>
                    <h2 className="text-2xl font-extrabold text-amber-800">Sentez Merkezi: Sıralı Kod Revizyonları</h2>
                    <p className="text-sm text-amber-700">Her komitenin sentezi sırayla işlendi. Önceki komitenin kararları sonrakine bağlam olarak iletildi.</p>
                  </div>
                </div>

                {makerBotRevisions.map((rev, rIdx) => {
                  const allMd = `# 📋 Briefing\n\n${rev.brief}\n\n---\n\n# 🔧 Revizyon\n\n${rev.revision}`;
                  return (
                    <div key={rIdx} className="mb-6 bg-gradient-to-br from-amber-50 to-orange-50 rounded-3xl border-2 border-amber-200 shadow-md overflow-hidden">
                      {/* Takım başlığı */}
                      <div className="bg-amber-700 text-white px-6 py-3 flex items-center justify-between">
                        <span className="font-bold text-lg">#{rIdx + 1} — {rev.team_name}</span>
                        <button
                          onClick={() => {
                            const blob = new Blob([allMd], { type: "text/markdown" });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = `${rev.team_name?.replace(/\s/g, "_")}_sentez_merkezi.md`;
                            a.click();
                            URL.revokeObjectURL(url);
                          }}
                          className="text-xs bg-white/20 hover:bg-white/30 px-3 py-1 rounded-lg font-medium transition-all"
                        >
                          ⬇️ MD indir
                        </button>
                      </div>

                      {/* Briefing */}
                      <details className="border-b border-amber-200">
                        <summary className="px-6 py-3 cursor-pointer font-semibold text-amber-800 hover:bg-amber-100 transition-colors select-none">
                          📋 Orkestratör Briefing (Sentez Merkezi'ne verilen talimat)
                        </summary>
                        <div className="px-6 pb-4 prose prose-sm max-w-none prose-headings:text-amber-800 prose-strong:text-amber-700">
                          <ReactMarkdown>{rev.brief}</ReactMarkdown>
                        </div>
                      </details>

                      {/* Revizyon */}
                      <div className="px-6 py-4 prose prose-base max-w-none prose-headings:text-slate-800 prose-pre:bg-[#0f172a] prose-pre:text-slate-200 prose-pre:p-4 prose-pre:rounded-xl">
                        <ReactMarkdown>{rev.revision}</ReactMarkdown>
                      </div>

                      {/* Aksiyonlar (Koda Uygula / İndir) */}
                      <div className="bg-white/40 border-t border-amber-200 px-6 py-4 flex items-center justify-end gap-3">
                        <button
                          onClick={() => {
                            const codeBlockRegex = /```[\w]*\n([\s\S]*?)```/g;
                            let matches = [];
                            let match;
                            while ((match = codeBlockRegex.exec(rev.revision)) !== null) {
                              matches.push(match[1].trim());
                            }
                            if (matches.length > 0) {
                              const combinedCode = matches.join("\n\n");
                              const blob = new Blob([combinedCode], { type: "text/plain" });
                              const url = URL.createObjectURL(blob);
                              const a = document.createElement("a");
                              a.href = url;
                              a.download = `${rev.team_name?.replace(/\s/g, "_")}_kod.txt`;
                              a.click();
                              URL.revokeObjectURL(url);
                            } else {
                              alert("İndirilecek kod bloğu bulunamadı.");
                            }
                          }}
                          className="text-sm font-bold text-amber-700 bg-white border-2 border-amber-200 hover:bg-amber-100 hover:border-amber-300 px-4 py-2 rounded-xl transition-all"
                        >
                          ⬇️ Sadece Kodu İndir
                        </button>
                        <button
                          onClick={() => {
                            const codeBlockRegex = /```[\w]*\n([\s\S]*?)```/g;
                            let matches = [];
                            let match;
                            while ((match = codeBlockRegex.exec(rev.revision)) !== null) {
                              matches.push(match[1].trim());
                            }
                            if (matches.length > 0) {
                              setInputCode(matches.join("\n\n"));
                              alert("✅ Revize edilen kodlar başarıyla 'Kod/Konsept' alanına aktarıldı. Şimdi sol panelden kurulları tekrar toplayarak yeni bir inceleme veya muhakeme başlatabilirsiniz.");
                            } else {
                              alert("⚠️ Uygulanacak herhangi bir kod bloğu bulunamadı.");
                            }
                          }}
                          className="text-sm font-bold text-white bg-amber-600 hover:bg-amber-700 px-5 py-2 rounded-xl transition-all shadow-md shadow-amber-200 hover:shadow-lg"
                        >
                          ⚡ Koda Uygula (Sol Panele Aktar)
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </main>
      </div>
      {/* Hakkında Modalı */}
      {aboutOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setAboutOpen(false)} />
          <div className="relative bg-white rounded-3xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-200 animate-in fade-in zoom-in duration-200">
            <div className="p-8">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-12 h-12 bg-teal-100 text-teal-700 rounded-2xl flex items-center justify-center text-2xl">ℹ️</div>
                <h2 className="text-2xl font-extrabold text-slate-800">Proje Hakkında</h2>
              </div>
              <p className="text-slate-600 leading-relaxed text-lg italic">
                "Bu proje Gazi Cyber CodeForge Hackathon 2026 bünyesinde 24 saat içerisinde Furkan Emir Kaya ve Görkem Şahinoğlu tarafından geliştirilmiştir."
              </p>
              <button
                onClick={() => setAboutOpen(false)}
                className="mt-8 w-full py-3 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 transition-colors"
              >
                Kapat
              </button>
            </div>
            <div className="h-2 bg-gradient-to-r from-teal-500 to-amber-500" />
          </div>
        </div>
      )}
    </div>
  );
}