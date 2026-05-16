# AI Judge — Sabit Değerler (Constants)
# Bu dosya backend genelinde kullanılan tüm sabit değerleri barındırır.
# Bir değeri değiştirmek için yalnızca bu dosyayı düzenlemeniz yeterlidir.

# ─────────────────────────────────────────
# Token & Karakter Limitleri
# ─────────────────────────────────────────
MAX_CODE_CHARS = 100_000       # ~25.000 token — yüklenen kod/proje içeriği
MAX_PROMPT_CHARS = 1_000       # ~250 token  — kullanıcı talimatı
MAX_DECISION_MAKER_CHARS = 3_000   # Karar Verici ajanına gönderilen kod özeti
MAX_ORCHESTRATOR_REPORT_CHARS = 1_500  # Orkestratör, her ajan raporundan bu kadar okur
MAX_MAKER_BOT_CONTEXT_CHARS = 800  # Maker Bot, önceki takım bağlamından bu kadarını alır

# ─────────────────────────────────────────
# Çalıştırma Parametreleri
# ─────────────────────────────────────────
MAX_ITERATIONS = 2             # Takım başına maksimum iterasyon (konsensüs turları)
STAGGER_DELAY_SECONDS = 2.0    # Ajan çağrıları arasındaki bekleme (rate-limit koruması)

# ─────────────────────────────────────────
# Dosya İşleme
# ─────────────────────────────────────────
TEXT_EXTENSIONS = frozenset({
    ".py", ".ts", ".tsx", ".js", ".jsx", ".txt", ".md", ".json",
    ".css", ".html", ".yaml", ".yml", ".env", ".toml", ".ini",
    ".c", ".cpp", ".h", ".java", ".go", ".rs", ".rb", ".php",
    ".swift", ".kt", ".dart", ".sql", ".sh", ".bat", ".ps1",
    ".xml", ".svg", ".vue", ".svelte", ".graphql", ".proto",
})

ZIP_SKIP_DIRS = (
    "node_modules/", ".git/", "__pycache__/",
    ".next/", "venv/", "dist/", "build/",
)

# ─────────────────────────────────────────
# Veritabanı
# ─────────────────────────────────────────
DB_NAME = "ai_judge.db"

# ─────────────────────────────────────────
# Varsayılan Takım (prompt verilmediğinde)
# ─────────────────────────────────────────
DEFAULT_TEAM = {
    "name": "Genel İnceleme Takımı",
    "focus_area": "Projenin tüm kısımlarını genel olarak analiz et.",
    "members": ["socrates", "alan_turing"],
}
