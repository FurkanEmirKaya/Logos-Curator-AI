"use client";
import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

export default function Home() {
  const [mounted, setMounted] = useState(false);
  const [inputCode, setInputCode] = useState("");
  const [userPrompt, setUserPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [personas, setPersonas] = useState<Record<string, any>>({});
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [reports, setReports] = useState<Record<string, string>>({});

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
        setReports(data.boards);
        if (data.ordered_agents) {
          setSelectedAgents(data.ordered_agents);
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
            <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto p-1">
              {Object.entries(personas).map(([id, meta]) => (
                <label key={id} className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-all ${selectedAgents.includes(id) ? 'bg-blue-50 border-blue-500 shadow-sm' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'}`}>
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
                </label>
              ))}
              {Object.keys(personas).length === 0 && (
                <div className="text-sm text-slate-400 animate-pulse">Kurul üyeleri salona davet ediliyor...</div>
              )}
            </div>
          </div>

          {/* Karar Verici Prompt Alanı */}
          <div className="mb-2">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Baş Karar Verici'ye Talimatınız (Opsiyonel)</h3>
            <textarea
              className="w-full h-20 p-3 border border-indigo-300 rounded-xl shadow-inner focus:ring-2 focus:ring-indigo-500 focus:outline-none font-sans text-sm resize-none bg-indigo-50"
              placeholder="Örn: Sadece frontend odaklı bir inceleme istiyorum. Tasarıma dikkat edin."
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
            />
            <p className="text-xs text-indigo-600 mt-1">Talimat girerseniz, kurullar talimatınıza göre Baş Karar Verici tarafından otomatik seçilir ve sıraya dizilir.</p>
          </div>

          <textarea
            className="w-full h-64 p-4 border border-slate-300 rounded-xl shadow-inner focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono text-sm resize-none bg-slate-50"
            placeholder="İncelemeye alınacak kodu veya uygulama konseptini buraya yapıştırın..."
            value={inputCode}
            onChange={(e) => setInputCode(e.target.value)}
          />
          <button
            onClick={handleAnalyze}
            disabled={!mounted || loading || !inputCode.trim() || (!userPrompt.trim() && selectedAgents.length === 0)}
            suppressHydrationWarning={true}
            className="mt-2 bg-slate-800 text-white font-bold py-3 px-6 rounded-xl hover:bg-blue-600 transition-all disabled:opacity-50 disabled:hover:bg-slate-800 flex justify-center items-center gap-2"
          >
            {loading ? (
              <span className="animate-pulse">Kurullar Tartışıyor (Lütfen Bekleyin)...</span>
            ) : (
              "İncelemeyi Başlat (Submit to Board)"
            )}
          </button>
        </div>

        {/* SAĞ PANEL: Kurul Raporları (Artifacts) */}
        <div className="flex flex-col gap-6 h-[80vh] overflow-y-auto pr-4 pb-12">

          {/* Bekleme / Boş Durum Ekranı */}
          {Object.keys(reports).length === 0 && !loading && (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-2xl bg-white/50 p-8 text-center">
              <span className="text-4xl mb-4">⚖️</span>
              <p>Raporlar burada görüntülenecektir.</p>
              <p className="text-sm mt-2 opacity-70">Sol panelden kurulları seçip analizi başlatın.</p>
            </div>
          )}

          {/* Yükleniyor Ekranı */}
          {loading && (
            <div className="h-full flex items-center justify-center text-blue-500 border-2 border-dashed border-blue-200 rounded-2xl bg-blue-50/50">
              <span className="animate-bounce text-2xl">⏳ Kurullar inceliyor...</span>
            </div>
          )}

          {/* DİNAMİK RAPORLAR */}
          {!loading && selectedAgents.map(agentId => {
            const reportContent = reports[agentId];
            if (!reportContent) return null;
            
            const meta = personas[agentId];
            if (!meta) return null;
            const colors = getBoardColor(meta.board);
            
            return (
              <div key={agentId} className="bg-white p-8 rounded-2xl shadow-md border-l-8" style={{ borderLeftColor: colors.border }}>
                <div className="flex items-center gap-3 mb-6 border-b pb-4">
                  <span className="text-3xl">{meta.icon}</span>
                  <div>
                    <h3 className="text-2xl font-bold" style={{ color: colors.text }}>{meta.display_name}</h3>
                    <p className="text-sm text-slate-500 font-medium">{meta.role}</p>
                  </div>
                </div>
                <div className="prose prose-slate max-w-none prose-headings:text-slate-800 prose-a:text-blue-600">
                  <ReactMarkdown>{reportContent}</ReactMarkdown>
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}