# AI Judge — UI Çeviri Haritaları
# Ajanlar (LLM) her zaman İngilizce metadata okur.
# Bu haritalar YALNIZCA /personas endpoint'i üzerinden frontend'e veri gönderilirken uygulanır.

# ─────────────────────────────────────────
# Persona Rol Çevirileri (EN → TR)
# ─────────────────────────────────────────
ROLE_TR: dict[str, str] = {
    "Usability Philosopher & Accessibility Auditor":                 "Kullanılabilirlik Filozofu ve Erişilebilirlik Denetçisi",
    "Visual Harmony Architect & Aesthetic-Function Synthesizer":     "Görsel Uyum Mimarı ve Estetik-Fonksiyon Sentezleyicisi",
    "Strategic Operations General & Efficiency Analyst":             "Stratejik Operasyon Generali ve Verimlilik Analisti",
    "API & Network Protocol Analyst & Integration Security Specialist": "API ve Ağ Protokolü Analisti ve Entegrasyon Güvenliği Uzmanı",
    "Leadership Strategy Consultant & Hierarchy Optimizer":          "Liderlik Stratejisi Danışmanı ve Hiyerarşi Optimize Edici",
    "Political Logic Auditor & Conflict Resolution Specialist":      "Siyasi Mantık Denetçisi ve Çatışma Çözümü Uzmanı",
    "Algorithm Logic Architect & Mathematical Consistency Auditor":  "Algoritma Mantığı Mimarı ve Matematiksel Tutarlılık Denetçisi",
    "Security Infrastructure Architect & Cryptographic Integrity Specialist": "Güvenlik Altyapısı Mimarı ve Kriptografik Bütünlük Uzmanı",
    "Cross-Platform Integration Specialist & Standardization Auditor": "Platformlar Arası Entegrasyon Uzmanı ve Standardizasyon Denetçisi",
    "Core Kernel Auditor & Performance Enforcement Specialist":      "Çekirdek Denetçisi ve Performans Uygulama Uzmanı",
    "Critical Systems Architect & Fault-Tolerance Specialist":       "Kritik Sistemler Mimarı ve Hata Toleransı Uzmanı",
    "Secure Wireless Communication & Logic Protocol Specialist":     "Güvenli Kablosuz İletişim ve Mantık Protokolü Uzmanı",
    "Product Vision Architect & Minimalist Experience Purist":       "Ürün Vizyonu Mimarı ve Minimalist Deneyim Tasarımcısı",
    "Performance Engineering Specialist & Resilience Auditor":       "Performans Mühendisliği Uzmanı ve Dayanıklılık Denetçisi",
    "Scientific Integrity Auditor & Technical Debt Researcher":      "Bilimsel Bütünlük Denetçisi ve Teknik Borç Araştırmacısı",
    "Narrative Experience Designer & Creative Engagement Architect": "Anlatı Deneyimi Tasarımcısı ve Yaratıcı Etkileşim Mimarı",
    "Inclusive Identity Designer & Visual Brand Auditor":            "Kapsayıcı Kimlik Tasarımcısı ve Görsel Marka Denetçisi",
    "Forensic Logic Auditor & Edge-Case Detective":                  "Adli Mantık Denetçisi ve Uç Durum Dedektifi",
    "QA Forensic Analyst & Edge Case Hunter":                        "QA Adli Analiz Uzmanı ve Uç Durum Avcısı",
    "Cultural Inclusivity Auditor & Visual Identity Specialist":     "Kültürel Kapsayıcılık Denetçisi ve Görsel Kimlik Uzmanı",
    "Onboarding Storyteller & Emotional Journey Designer":           "Onboarding Hikaye Anlatıcısı ve Duygusal Yolculuk Tasarımcısı",
    "Analytics Methodology Auditor & Evidence-Based Decision Analyst": "Analitik Metodoloji Denetçisi ve Kanıta Dayalı Karar Analisti",
    "Domain Accuracy Validator & Performance Data Integrity Analyst":"Alan Doğruluk Doğrulayıcısı ve Performans Veri Bütünlüğü Analisti",
    "Product Vision Director & User Experience Absolutist":          "Ürün Vizyonu Direktörü ve Kullanıcı Deneyimi Mutlakiyetçisi",
    "Testing Strategist & Mission-Critical Reliability Engineer":    "Test Stratejisti ve Kritik Görev Güvenilirlik Mühendisi",
    "Code Quality Enforcer & Platform Engineering Critic":           "Kod Kalitesi Denetçisi ve Platform Mühendisliği Eleştirmeni",
    "Backend Performance Engineer & System Optimization Specialist": "Backend Performans Mühendisi ve Sistem Optimizasyon Uzmanı",
    "Security Auditor & Logical Integrity Validator":                "Güvenlik Denetçisi ve Mantıksal Bütünlük Doğrulayıcısı",
    "Code Architecture Analyst & Design Pattern Enforcer":           "Kod Mimarisi Analisti ve Tasarım Kalıbı Denetçisi",
    "Growth Hacking Strategist & Monetization Architect":            "Büyüme Stratejisti ve Gelir Modeli Mimarı",
    "Brand Positioning Strategist & Cultural Adaptation Specialist": "Marka Konumlandırma Stratejisti ve Kültürel Adaptasyon Uzmanı",
    "Scalability Architect & Technical Futurist":                    "Ölçeklenebilirlik Mimarı ve Teknik Fütürist",
    "Competitive Strategy Analyst & Risk Warfare Advisor":           "Rekabetçi Strateji Analisti ve Risk Savaşı Danışmanı",
}

# ─────────────────────────────────────────
# Uzmanlık Alanı Çevirileri (EN → TR)
# ─────────────────────────────────────────
EXP_TR: dict[str, str] = {
    # Genel Yazılım
    "UX": "UX", "WCAG": "WCAG", "OWASP": "OWASP", "QA": "QA",
    "SOLID": "SOLID", "CI_CD": "CI/CD", "git": "git", "devops": "devops",

    # Frontend / UI
    "accessibility": "erişilebilirlik", "navigation": "navigasyon",
    "cognitive_load": "bilişsel_yük", "visual_design": "görsel_tasarım",
    "layout": "düzen", "color_theory": "renk_teorisi", "typography": "tipografi",
    "motion_design": "hareket_tasarımı", "design_systems": "tasarım_sistemleri",
    "minimalism": "minimalizm", "emotional_design": "duygusal_tasarım",
    "narrative_UX": "anlatısal_UX", "expert_UX": "uzman_UX",
    "visual_identity": "görsel_kimlik",

    # Backend / Sistem
    "backend": "backend", "performance": "performans", "optimization": "optimizasyon",
    "scalability": "ölçeklenebilirlik", "architecture": "mimari",
    "system_architecture": "sistem_mimarisi", "infrastructure": "altyapı",
    "databases": "veritabanları", "monitoring": "izleme", "debugging": "hata_ayıklama",
    "kernel": "kernel", "low_level": "düşük_seviye",
    "build_systems": "derleme_sistemleri", "platform_engineering": "platform_mühendisliği",
    "modularity": "modülerlik", "future_proofing": "geleceğe_hazırlık",

    # Güvenlik
    "security": "güvenlik", "cryptography": "kriptografi",
    "authentication": "kimlik_doğrulama", "input_validation": "girdi_doğrulama",
    "data_protection": "veri_koruma", "wireless": "kablosuz",

    # Ağ / Entegrasyon
    "API_design": "API_tasarımı", "protocols": "protokoller",
    "real_time": "gerçek_zamanlı", "WebSocket": "WebSocket",
    "cross_platform": "platformlar_arası", "integration": "entegrasyon",
    "standardization": "standartlaştırma", "legacy_systems": "eski_sistemler",

    # Yazılım Kalitesi
    "code_quality": "kod_kalitesi", "clean_code": "temiz_kod",
    "design_patterns": "tasarım_kalıpları", "refactoring": "yeniden_yapılandırma",
    "documentation": "dokümantasyon", "code_review": "kod_incelemesi",
    "testing": "test", "fault_tolerance": "hata_toleransı",
    "error_handling": "hata_yönetimi", "reliability": "güvenilirlik",
    "resilience": "dayanıklılık", "edge_cases": "uç_durumlar",

    # Test / QA
    "forensics": "adli_analiz", "stress_testing": "stres_testi",
    "cross_browser": "tarayıcı_uyumluluğu", "regression": "regresyon",
    "bug_hunting": "hata_avcılığı", "performance_metrics": "performans_metrikleri",

    # Algoritma / Matematik
    "algorithm_design": "algoritma_tasarımı", "mathematics": "matematik",
    "computability": "hesaplanabilirlik", "logic": "mantık",
    "game_theory": "oyun_teorisi",

    # Strateji / İş
    "strategy": "strateji", "monetization": "gelir_modeli",
    "growth_hacking": "büyüme", "pricing_strategy": "fiyatlandırma_stratejisi",
    "viral_mechanics": "viral_mekanikler", "retention": "kullanıcıyı_elde_tutma",
    "product_vision": "ürün_vizyonu", "product_market_fit": "ürün_pazar_uyumu",
    "feature_prioritization": "özellik_önceliklendirme",
    "platform_strategy": "platform_stratejisi",
    "competitive_analysis": "rekabet_analizi",
    "market_positioning": "pazar_konumlandırması",
    "MVP_strategy": "MVP_stratejisi", "risk_assessment": "risk_değerlendirmesi",
    "risk_management": "risk_yönetimi", "innovation": "inovasyon",

    # Liderlik / Organizasyon
    "leadership": "liderlik", "hierarchy": "hiyerarşi",
    "governance": "yönetişim", "conflict_resolution": "çatışma_çözümü",
    "psychology": "psikoloji", "ethics": "etik",

    # Analitik / Veri
    "analytics": "analitik", "statistics": "istatistik",
    "A_B_testing": "A/B_testleri", "KPIs": "KPI_metrikleri",
    "user_segmentation": "kullanıcı_segmentasyonu", "cohort_analysis": "kohort_analizi",
    "data_science": "veri_bilimi", "data_integrity": "veri_bütünlüğü",
    "real_time_data": "gerçek_zamanlı_veri", "domain_accuracy": "alan_doğruluğu",
    "industry_standards": "endüstri_standartları", "evidence_gathering": "kanıt_toplama",
    "accuracy": "doğruluk", "research": "araştırma",

    # Marka / Kültür
    "branding": "markalaşma", "positioning": "konumlandırma",
    "localization": "yerelleştirme", "cultural_adaptation": "kültürel_adaptasyon",
    "audience_segmentation": "hedef_kitle_segmentasyonu", "copywriting": "metin_yazarlığı",
    "culture": "kültür", "diversity": "çeşitlilik", "inclusivity": "kapsayıcılık",
    "representation": "temsil", "ethical_design": "etik_tasarım",
    "cultural_sensitivity": "kültürel_duyarlılık",

    # Deneyim Tasarımı
    "storytelling": "hikaye_anlatımı", "gamification": "oyunlaştırma",
    "onboarding": "onboarding", "engagement": "etkileşim",
}
