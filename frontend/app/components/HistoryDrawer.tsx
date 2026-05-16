"use client";
import { useState, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";

const API = "http://localhost:8001";

interface SessionSummary {
  id: number;
  timestamp: string;
  user_prompt: string;
}

interface TeamData {
  name: string;
  focus_area: string;
  final_synthesis: string;
  reports: Record<string, string>;
  maker_bot_brief?: string;
  iterations?: any[];
}

interface SessionDetail {
  id: number;
  timestamp: string;
  user_prompt: string;
  teams: TeamData[];
  dependencies_md: string;
  codemap_md: string;
}

type Tab = "dependencies" | "codemap" | `team_${number}` | `brief_${number}`;

function formatDate(ts: string) {
  if (!ts) return "";
  const d = new Date(ts.includes("T") ? ts : ts + "Z");
  return d.toLocaleString("tr-TR", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function MdPanel({ content, emptyText }: { content: string; emptyText: string }) {
  if (!content) return (
    <div className="flex items-center justify-center h-40 text-slate-400 text-sm italic">
      {emptyText}
    </div>
  );
  return (
    <div className="prose prose-base max-w-none prose-headings:text-slate-800 prose-strong:text-slate-700 prose-table:text-xs">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}

export default function HistoryDrawer({
  isOpen,
  onClose,
  currentSession,
}: {
  isOpen: boolean;
  onClose: () => void;
  currentSession: SessionDetail | null;
}) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selected, setSelected] = useState<SessionDetail | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("dependencies");
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingList, setLoadingList] = useState(false);

  const fetchSessions = useCallback(async () => {
    setLoadingList(true);
    try {
      const r = await fetch(`${API}/sessions`);
      const d = await r.json();
      if (d.status === "success") setSessions(d.sessions);
    } catch (_) { }
    setLoadingList(false);
  }, []);

  useEffect(() => {
    if (isOpen) fetchSessions();
  }, [isOpen, fetchSessions]);

  // Yeni analiz gelince listeyi güncelle ve onu seç
  useEffect(() => {
    if (currentSession) {
      setSelected(currentSession);
      setActiveTab("dependencies");
      fetchSessions();
    }
  }, [currentSession, fetchSessions]);

  const openSession = async (id: number) => {
    setLoadingDetail(true);
    try {
      const r = await fetch(`${API}/sessions/${id}`);
      const d = await r.json();
      if (d.status === "success") {
        setSelected(d.session);
        setActiveTab("dependencies");
      }
    } catch (_) { }
    setLoadingDetail(false);
  };

  const sel = selected;
  const tabCount = sel
    ? 2 + sel.teams.length + sel.teams.filter((t) => t.maker_bot_brief).length
    : 0;

  const tabs: { id: Tab; label: string; emoji: string }[] = sel
    ? [
      { id: "dependencies", label: "Bağımlılıklar", emoji: "📦" },
      { id: "codemap", label: "Kod Haritası", emoji: "🗺️" },
      ...sel.teams.map((t, i) => ({
        id: `team_${i}` as Tab,
        label: t.name,
        emoji: "👥",
      })),
      ...sel.teams
        .map((t, i) =>
          t.maker_bot_brief
            ? { id: `brief_${i}` as Tab, label: `${t.name} — Talimat`, emoji: "📋" }
            : null
        )
        .filter(Boolean) as { id: Tab; label: string; emoji: string }[],
    ]
    : [];

  function renderContent() {
    if (!sel) return null;
    if (activeTab === "dependencies")
      return <MdPanel content={sel.dependencies_md} emptyText="Bu oturum için bağımlılık raporu mevcut değil." />;
    if (activeTab === "codemap")
      return <MdPanel content={sel.codemap_md} emptyText="Bu oturum için kod haritası mevcut değil." />;

    const m = activeTab.match(/^team_(\d+)$/);
    if (m) {
      const t = sel.teams[+m[1]];
      if (!t) return null;
      return (
        <div>
          {t.final_synthesis && (
            <div className="mb-4 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
              <p className="text-sm font-bold text-emerald-700 mb-1">🤝 Uzlaşı Özeti</p>
              <p className="text-base text-emerald-800">{t.final_synthesis}</p>
            </div>
          )}
          {Object.entries(t.reports).map(([aid, report]) => (
            <details key={aid} className="mb-3 border border-slate-200 rounded-xl overflow-hidden">
              <summary className="px-4 py-3 bg-slate-50 cursor-pointer font-semibold text-slate-700 text-base hover:bg-slate-100 transition-colors">
                🧑‍💼 {aid}
              </summary>
              <div className="px-4 py-3 prose prose-base max-w-none">
                <ReactMarkdown>{report as string}</ReactMarkdown>
              </div>
            </details>
          ))}
        </div>
      );
    }

    const bm = activeTab.match(/^brief_(\d+)$/);
    if (bm) {
      const t = sel.teams[+bm[1]];
      if (!t) return null;
      return <MdPanel content={t.maker_bot_brief || ""} emptyText="Talimat bulunamadı." />;
    }
    return null;
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/30 backdrop-blur-sm z-[60] transition-opacity duration-300 ${isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
          }`}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={`fixed top-0 left-0 h-full z-[70] flex shadow-2xl transition-transform duration-300 ease-in-out ${isOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        style={{ width: "min(960px, 92vw)" }}
      >
        {/* ── Sol: Oturum Listesi ── */}
        <div className="w-72 flex-shrink-0 bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col">
          {/* Header */}
          <div className="px-5 pt-6 pb-4 border-b border-slate-700">
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-white font-extrabold text-2xl tracking-tight flex items-center gap-2">
                <span className="text-3xl">🏛️</span>
                <span>Curator <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-amber-500">AI</span></span>
              </h2>
              <button
                onClick={onClose}
                className="text-slate-400 hover:text-white transition-colors text-xl leading-none"
                aria-label="Kapat"
              >
                ✕
              </button>
            </div>
            <p className="text-slate-400 text-xs">Analiz Geçmişi</p>
          </div>

          {/* Session List */}
          <div className="flex-1 overflow-y-auto py-3 px-3 flex flex-col gap-2">
            {loadingList && (
              <p className="text-slate-400 text-xs text-center pt-6 animate-pulse">Yükleniyor...</p>
            )}
            {!loadingList && sessions.length === 0 && (
              <p className="text-slate-500 text-xs text-center pt-6 italic">
                Henüz kayıtlı analiz yok.
              </p>
            )}
            {sessions.map((s) => {
              const isActive = sel?.id === s.id;
              return (
                <div key={s.id} className="flex items-center gap-1 group/item">
                  <button
                    onClick={() => openSession(s.id)}
                    className={`flex-1 text-left px-4 py-3 rounded-xl transition-all duration-150 group ${isActive
                        ? "bg-indigo-600 shadow-lg shadow-indigo-900/40"
                        : "hover:bg-slate-700/70"
                      }`}
                  >
                    <p className={`text-sm font-semibold mb-1 line-clamp-2 ${isActive ? "text-white" : "text-slate-200"}`}>
                      {s.user_prompt || "(Prompt girilmedi)"}
                    </p>
                    <p className={`text-xs ${isActive ? "text-indigo-200" : "text-slate-500"}`}>
                      🕐 {formatDate(s.timestamp)}
                    </p>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(`http://localhost:8001/sessions/${s.id}/report`, '_blank');
                    }}
                    className="p-3 bg-indigo-500 text-white hover:bg-indigo-400 rounded-xl transition-all opacity-0 group-hover/item:opacity-100 focus:opacity-100 shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40 flex items-center justify-center min-w-[44px]"
                    title="Raporu İndir (.md)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>

          <div className="px-4 py-3 border-t border-slate-700">
            <button
              onClick={fetchSessions}
              className="w-full text-center text-slate-400 hover:text-white text-xs py-2 transition-colors"
            >
              ↺ Listeyi Yenile
            </button>
          </div>
        </div>

        {/* ── Sağ: Artifact Görüntüleyici ── */}
        <div className="flex-1 bg-white flex flex-col min-w-0">
          {!sel && !loadingDetail && (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-300 gap-4">
              <span className="text-6xl">📄</span>
              <p className="text-sm font-medium text-slate-400">
                Görüntülemek için sol panelden bir oturum seçin.
              </p>
            </div>
          )}

          {loadingDetail && (
            <div className="flex-1 flex items-center justify-center text-indigo-400 animate-pulse text-sm">
              Oturum yükleniyor...
            </div>
          )}

          {sel && !loadingDetail && (
            <>
              {/* Session Header */}
              <div className="px-6 pt-5 pb-3 border-b border-slate-200 bg-slate-50">
                <p className="text-[11px] text-slate-400 font-mono mb-1">
                  #{sel.id} · {formatDate(sel.timestamp)}
                </p>
                <h3 className="text-lg font-bold text-slate-800 line-clamp-2">
                  {sel.user_prompt || "(Prompt girilmedi)"}
                </h3>
                <p className="text-sm text-slate-500 mt-1">
                  {sel.teams.length} takım · {tabCount} belge
                </p>
              </div>

              {/* Tabs — Geliştirilmiş Tasarım */}
              <div className="flex gap-2 px-4 py-3 overflow-x-auto border-b border-slate-200 bg-slate-50/50 flex-shrink-0 scrollbar-thin scrollbar-thumb-slate-200">
                {tabs.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setActiveTab(t.id)}
                    className={`whitespace-nowrap px-5 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center gap-2 border ${activeTab === t.id
                        ? "bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-200 scale-[1.02]"
                        : "bg-white text-slate-600 border-slate-200 hover:border-indigo-300 hover:bg-white hover:shadow-sm"
                      }`}
                  >
                    <span className="text-base">{t.emoji}</span>
                    <span>{t.label}</span>
                  </button>
                ))}
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto px-6 py-5">
                {renderContent()}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
