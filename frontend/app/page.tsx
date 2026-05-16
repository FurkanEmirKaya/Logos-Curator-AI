"use client";
import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

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
        <div className="inline-block bg-white text-indigo-700 text-sm font-medium px-4 py-2 rounded-xl border border-indigo-200 shadow-sm">
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
        <div className="mb-6 p-5 bg-emerald-50 border border-emerald-200 rounded-xl shadow-sm">
          <h3 className="font-bold text-emerald-800 mb-1 flex items-center gap-2">
            <span>🤝</span> Takım Uzlaşı Özeti
          </h3>
          <p className="text-sm text-emerald-700 leading-relaxed">{team.final_synthesis}</p>
        </div>
      )}

      {currentIter.consensus_result && !currentIter.consensus_result.consensus_reached && (
        <div className="mb-6 p-5 bg-amber-50 border border-amber-200 rounded-xl shadow-sm">
          <h3 className="font-bold text-amber-800 mb-1 flex items-center gap-2">
            <span>⚠️</span> Moderatör Geri Bildirimi (Çelişki Tespit Edildi)
          </h3>
          <p className="text-sm text-amber-700 leading-relaxed">{currentIter.consensus_result.feedback}</p>
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
              <div className="prose prose-sm md:prose-base prose-slate max-w-none prose-headings:text-slate-800 prose-a:text-blue-600">
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

  const MAX_CODE_CHARS = 15000;
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

        // Seçili ajanları (checkboxlar için) güncelle
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
          alert(`⚠️ "${data.filename}" içeriği 15.000 karakter limitinde kesildi.`);
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

  const getBoardColor = (boardName: string) => {
    if (boardName === "historical_thinkers") return { border: "#f59e0b", text: "#b45309" }; // amber
    if (boardName === "technical_experts") return { border: "#3b82f6", text: "#1d4ed8" }; // blue
    return { border: "#10b981", text: "#047857" }; // emerald
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-8 font-sans">
      <header className="mb-8 border-b pb-4">
        <h1 className="text-4xl font-extrabold text-slate-800 tracking-tight">AI Judge <span className="text-blue-600">Komite Odası</span></h1>
        <p className="text-slate-500 mt-2 text-lg">Projenizi sisteme yükleyin, uzman kurullarımız inceleyip raporlasın.</p>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* SOL PANEL: Girdi Alanı */}
        <div className="flex flex-col gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <h2 className="text-xl font-bold text-slate-700">İncelenecek Kod / Prototip</h2>

          {/* Ajan Seçimi */}
          <div className="mb-2">
            <h3 className="text-sm font-semibold text-slate-500 mb-2 uppercase tracking-wider">İnceleme Kurulunu Seçin</h3>
            <div className="flex flex-wrap gap-2 p-1">
              {Object.entries(personas).map(([id, meta]) => (
                <label key={id} className={`group relative flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-all ${selectedAgents.includes(id) ? 'bg-blue-50 border-blue-500 shadow-sm' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'}`}>
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={selectedAgents.includes(id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedAgents([...selectedAgents, id]);
                      } else {
                        setSelectedAgents(selectedAgents.filter(a => a !== id));
                      }
                    }}
                  />
                  <span className="text-xl">{meta.icon}</span>
                  <span className="text-sm font-medium text-slate-800">{meta.display_name}</span>

                  {/* Hover Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-3 bg-slate-800 text-white text-xs rounded-xl shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                    <p className="font-bold text-blue-300 mb-1">{meta.role}</p>
                    <p className="text-slate-300 leading-relaxed line-clamp-3">
                      <span className="font-semibold text-slate-400">Uzmanlık:</span> {meta.expertise?.join(', ')}
                    </p>
                    {/* Küçük ok işareti */}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800"></div>
                  </div>
                </label>
              ))}
              {Object.keys(personas).length === 0 && (
                <div className="text-sm text-slate-400 animate-pulse">Kurul üyeleri salona davet ediliyor...</div>
              )}
            </div>
          </div>

          {/* Dosya Yükleme */}
          <div className="mb-2">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Dosya Yükle (Opsiyonel)</h3>
            <label className="flex flex-col items-center justify-center w-full h-20 border-2 border-dashed border-slate-300 rounded-xl cursor-pointer bg-slate-50 hover:bg-blue-50 hover:border-blue-400 transition-all">
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
                  <span key={i} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">📄 {f}</span>
                ))}
              </div>
            )}
          </div>

          {/* Karar Verici Prompt Alanı */}
          <div className="mb-2">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-sm font-semibold text-slate-700">Baş Karar Verici'ye Talimatınız (Opsiyonel)</h3>
              <span className={`text-xs font-mono ${userPrompt.length > MAX_PROMPT_CHARS * 0.85 ? 'text-red-500 font-bold' : 'text-slate-400'}`}>
                {userPrompt.length}/{MAX_PROMPT_CHARS}
              </span>
            </div>
            <textarea
              className="w-full h-20 p-3 border border-indigo-300 rounded-xl shadow-inner focus:ring-2 focus:ring-indigo-500 focus:outline-none font-sans text-sm resize-none bg-indigo-50"
              placeholder="Örn: Sadece frontend odaklı bir inceleme istiyorum. Tasarıma dikkat edin."
              maxLength={MAX_PROMPT_CHARS}
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
            />
            <p className="text-xs text-indigo-600 mt-1">Talimat girerseniz, kurullar talimatınıza göre Baş Karar Verici tarafından otomatik seçilir ve sıraya dizilir.</p>
          </div>

          <div className="relative mb-2">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-slate-400 font-medium">Kod / Konsept</span>
              <span className={`text-xs font-mono ${inputCode.length > MAX_CODE_CHARS * 0.9 ? 'text-red-500 font-bold' : 'text-slate-400'}`}>
                {inputCode.length.toLocaleString()}/{MAX_CODE_CHARS.toLocaleString()} karakter
              </span>
            </div>
            <textarea
              className="w-full h-64 p-4 border border-slate-300 rounded-xl shadow-inner focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono text-sm resize-none bg-slate-50"
              placeholder="İncelemeye alınacak kodu veya uygulama konseptini buraya yapıştırın..."
              maxLength={MAX_CODE_CHARS}
              value={inputCode}
              onChange={(e) => setInputCode(e.target.value)}
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={!mounted || loading || !inputCode.trim() || (!userPrompt.trim() && selectedAgents.length === 0)}
            suppressHydrationWarning={true}
            className="mt-2 bg-slate-800 text-white font-bold py-3 px-6 rounded-xl hover:bg-blue-600 transition-all disabled:opacity-50 disabled:hover:bg-slate-800 flex justify-center items-center gap-2"
          >
            {loading ? (
              <span className="animate-pulse">Kurullar Tartışıyor (Lütfen Bekleyin)...</span>
            ) : (
              "İncelemeyi Başlat"
            )}
          </button>
          
          {/* Maker Bot Butonu - Sadece analiz tamamlandıktan sonra görünür */}
          {teamReports.length > 0 && (
            <button
              onClick={handleMakerBot}
              disabled={makerBotLoading}
              className="mt-2 w-full bg-gradient-to-r from-violet-600 to-indigo-600 text-white font-bold py-3 px-6 rounded-xl hover:from-violet-700 hover:to-indigo-700 transition-all disabled:opacity-50 flex justify-center items-center gap-2 shadow-lg"
            >
              {makerBotLoading ? (
                <span className="animate-pulse">⚙️ Maker Bot Sentezliyor...</span>
              ) : (
                <span>🤖 Maker Bot: Nihai Revizyon Planı Üret</span>
              )}
            </button>
          )}
        </div>

        {/* SAĞ PANEL: Kurul Raporları (Artifacts) */}
        <div className="flex flex-col gap-6 h-[80vh] overflow-y-auto pr-4 pb-12">

          {/* Bekleme / Boş Durum Ekranı */}
          {teamReports.length === 0 && !loading && (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-2xl bg-white/50 p-8 text-center">
              <span className="text-4xl mb-4">⚖️</span>
              <p>Takım raporları burada görüntülenecektir.</p>
              <p className="text-sm mt-2 opacity-70">Sol panelden talimatınızı verin ve analizi başlatın.</p>
            </div>
          )}

          {/* Yükleniyor Ekranı */}
          {loading && (
            <div className="h-full flex items-center justify-center text-blue-500 border-2 border-dashed border-blue-200 rounded-2xl bg-blue-50/50">
              <span className="animate-bounce text-2xl">⏳ Takımlar kuruluyor ve kod inceleniyor...</span>
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
                  <h2 className="text-2xl font-extrabold text-violet-800">Maker Bot: Sıralı Kod Revizyonları</h2>
                  <p className="text-sm text-violet-600">Her takımın briefing'i sırayla işlendi. Önceki takımın değişiklikleri sonrakine bağlam olarak iletildi.</p>
                </div>
              </div>
              
              {makerBotRevisions.map((rev, rIdx) => {
                const allMd = `# 📋 Briefing\n\n${rev.brief}\n\n---\n\n# 🔧 Revizyon\n\n${rev.revision}`;
                return (
                  <div key={rIdx} className="mb-6 bg-gradient-to-br from-violet-50 to-indigo-50 rounded-3xl border-2 border-violet-200 shadow-md overflow-hidden">
                    {/* Takım başlığı */}
                    <div className="bg-violet-700 text-white px-6 py-3 flex items-center justify-between">
                      <span className="font-bold text-lg">#{rIdx + 1} — {rev.team_name}</span>
                      <button
                        onClick={() => {
                          const blob = new Blob([allMd], { type: "text/markdown" });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement("a");
                          a.href = url;
                          a.download = `${rev.team_name?.replace(/\s/g,"_")}_maker_bot.md`;
                          a.click();
                          URL.revokeObjectURL(url);
                        }}
                        className="text-xs bg-white/20 hover:bg-white/30 px-3 py-1 rounded-lg font-medium transition-all"
                      >
                        ⬇️ MD indir
                      </button>
                    </div>
                    
                    {/* Briefing */}
                    <details className="border-b border-violet-200">
                      <summary className="px-6 py-3 cursor-pointer font-semibold text-violet-800 hover:bg-violet-100 transition-colors select-none">
                        📋 Orkestratör Briefing (Maker Bot'a verilen talimat)
                      </summary>
                      <div className="px-6 pb-4 prose prose-sm max-w-none prose-headings:text-violet-800 prose-strong:text-violet-700">
                        <ReactMarkdown>{rev.brief}</ReactMarkdown>
                      </div>
                    </details>
                    
                    {/* Revizyon */}
                    <div className="px-6 py-4 prose prose-sm md:prose-base max-w-none prose-headings:text-slate-800 prose-code:bg-slate-100 prose-pre:bg-slate-900 prose-pre:text-green-300">
                      <ReactMarkdown>{rev.revision}</ReactMarkdown>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}