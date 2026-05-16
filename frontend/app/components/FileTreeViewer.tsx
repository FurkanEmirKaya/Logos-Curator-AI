"use client";
import { useState } from "react";

export interface GenFile { path: string; content: string; lang: string; }

const API = "http://localhost:8001";

function buildTree(files: GenFile[]) {
  const tree: Record<string, GenFile[]> = {};
  files.forEach(f => {
    const parts = f.path.split("/");
    const dir = parts.length > 1 ? parts.slice(0, -1).join("/") : "";
    if (!tree[dir]) tree[dir] = [];
    tree[dir].push(f);
  });
  return tree;
}

export function parseGeneratedFiles(raw: string): GenFile[] {
  const files: GenFile[] = [];
  const regex = /## 📄 ([^\n]+)\n```(\w*)\n([\s\S]+?)```/g;
  let m: RegExpExecArray | null;
  while ((m = regex.exec(raw)) !== null) {
    files.push({ path: m[1].trim(), lang: m[2] || "text", content: m[3] });
  }
  return files;
}

export default function FileTreeViewer({ files }: { files: GenFile[] }) {
  const [selected, setSelected] = useState<string>(files[0]?.path ?? "");
  const [downloading, setDownloading] = useState(false);

  const tree = buildTree(files);
  const selFile = files.find(f => f.path === selected);

  const downloadZip = async () => {
    setDownloading(true);
    try {
      const res = await fetch(`${API}/generate/download-zip`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files: files.map(f => ({ path: f.path, content: f.content })) }),
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "generated_project.zip"; a.click();
      URL.revokeObjectURL(url);
    } catch { alert("ZIP indirme hatası!"); }
    setDownloading(false);
  };

  if (files.length === 0)
    return (
      <div className="h-64 flex items-center justify-center rounded-3xl text-lg font-medium"
        style={{ border: "2px dashed #c7d2fe", background: "#f5f7ff", color: "#818cf8" }}>
        Henüz dosya üretilmedi.
      </div>
    );

  return (
    <div className="flex rounded-3xl overflow-hidden shadow-md" style={{ border: "1.5px solid #e0e7ff", minHeight: 420 }}>
      {/* Sol: Dosya ağacı */}
      <div className="w-56 flex-shrink-0 flex flex-col" style={{ background: "#1e1b4b" }}>
        <div className="p-3" style={{ borderBottom: "1px solid #312e81" }}>
          <button
            onClick={downloadZip}
            disabled={downloading}
            className="w-full py-2.5 rounded-xl text-sm font-bold text-white transition-all disabled:opacity-60"
            style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)" }}
          >
            {downloading ? "⏳ İndiriliyor..." : "⬇️ ZIP İndir"}
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {Object.entries(tree).map(([dir, dirFiles]) => (
            <div key={dir}>
              {dir && (
                <div className="px-4 py-1.5 text-sm font-bold uppercase tracking-wider" style={{ color: "#a5b4fc" }}>
                  📁 {dir}
                </div>
              )}
              {dirFiles.map(f => (
                <button
                  key={f.path}
                  onClick={() => setSelected(f.path)}
                  className="w-full text-left px-5 py-2 text-sm truncate transition-colors"
                  style={{
                    color: selected === f.path ? "#fff" : "#c7d2fe",
                    background: selected === f.path ? "#4f46e5" : "transparent",
                    fontWeight: selected === f.path ? 600 : 400,
                  }}
                >
                  📄 {f.path.split("/").pop()}
                </button>
              ))}
            </div>
          ))}
        </div>
        <div className="px-4 py-3 text-xs text-center" style={{ color: "#6366f1", borderTop: "1px solid #312e81" }}>
          {files.length} dosya üretildi
        </div>
      </div>

      {/* Sağ: Dosya içeriği */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selFile ? (
          <>
            <div className="flex items-center justify-between px-5 py-3" style={{ borderBottom: "1px solid #e0e7ff", background: "#f8faff" }}>
              <span className="text-base font-bold" style={{ color: "#1e1b4b" }}>{selFile.path}</span>
              <span className="text-sm px-2 py-1 rounded-lg" style={{ background: "#eef2ff", color: "#6366f1" }}>{selFile.lang}</span>
            </div>
            <pre className="flex-1 overflow-auto p-5 text-sm font-mono leading-relaxed"
              style={{ background: "#0f0f23", color: "#a5f3fc", margin: 0 }}>
              <code>{selFile.content}</code>
            </pre>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400">
            Sol taraftan bir dosya seçin
          </div>
        )}
      </div>
    </div>
  );
}
