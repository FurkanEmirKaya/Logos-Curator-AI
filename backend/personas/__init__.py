"""
AI Judge — Persona Loader
Imports all 18 persona system prompts and metadata for LangChain agent orchestration.
"""

import importlib

def _load(module_name, prefix):
    mod = importlib.import_module(f".prompts.{module_name}", package=__name__)
    return getattr(mod, f"{prefix}_SYSTEM_PROMPT"), getattr(mod, f"{prefix}_METADATA")

# === BOARD 1: Historical Thinkers & Philosophers ===
SOCRATES_SYSTEM_PROMPT, SOCRATES_METADATA = _load("01_socrates", "SOCRATES")
DAVINCI_SYSTEM_PROMPT, DAVINCI_METADATA = _load("02_davinci", "DAVINCI")
SUN_TZU_SYSTEM_PROMPT, SUN_TZU_METADATA = _load("03_sun_tzu", "SUN_TZU")
TESLA_SYSTEM_PROMPT, TESLA_METADATA = _load("04_tesla", "TESLA")
CLEOPATRA_SYSTEM_PROMPT, CLEOPATRA_METADATA = _load("05_cleopatra", "CLEOPATRA")
MACHIAVELLI_SYSTEM_PROMPT, MACHIAVELLI_METADATA = _load("06_machiavelli", "MACHIAVELLI")

# === BOARD 2: Technical Development Experts ===
ADA_LOVELACE_SYSTEM_PROMPT, ADA_LOVELACE_METADATA = _load("07_ada_lovelace", "ADA_LOVELACE")
ALAN_TURING_SYSTEM_PROMPT, ALAN_TURING_METADATA = _load("08_alan_turing", "ALAN_TURING")
GRACE_HOPPER_SYSTEM_PROMPT, GRACE_HOPPER_METADATA = _load("09_grace_hopper", "GRACE_HOPPER")
LINUS_TORVALDS_SYSTEM_PROMPT, LINUS_TORVALDS_METADATA = _load("10_linus_torvalds", "LINUS_TORVALDS")
MARGARET_HAMILTON_SYSTEM_PROMPT, MARGARET_HAMILTON_METADATA = _load("11_margaret_hamilton", "MARGARET_HAMILTON")
HEDY_LAMARR_SYSTEM_PROMPT, HEDY_LAMARR_METADATA = _load("12_hedy_lamarr", "HEDY_LAMARR")

# === BOARD 3: Market & Audience Analysts ===
STEVE_JOBS_SYSTEM_PROMPT, STEVE_JOBS_METADATA = _load("13_steve_jobs", "STEVE_JOBS")
NIKI_LAUDA_SYSTEM_PROMPT, NIKI_LAUDA_METADATA = _load("14_niki_lauda", "NIKI_LAUDA")
MARIE_CURIE_SYSTEM_PROMPT, MARIE_CURIE_METADATA = _load("15_marie_curie", "MARIE_CURIE")
WALT_DISNEY_SYSTEM_PROMPT, WALT_DISNEY_METADATA = _load("16_walt_disney", "WALT_DISNEY")
FRIDA_KAHLO_SYSTEM_PROMPT, FRIDA_KAHLO_METADATA = _load("17_frida_kahlo", "FRIDA_KAHLO")
SHERLOCK_HOLMES_SYSTEM_PROMPT, SHERLOCK_HOLMES_METADATA = _load("18_sherlock_holmes", "SHERLOCK_HOLMES")


# === MASTER REGISTRY ===

PERSONA_REGISTRY = {
    # Board 1
    "socrates": {"prompt": SOCRATES_SYSTEM_PROMPT, "meta": SOCRATES_METADATA},
    "leonardo_da_vinci": {"prompt": DAVINCI_SYSTEM_PROMPT, "meta": DAVINCI_METADATA},
    "sun_tzu": {"prompt": SUN_TZU_SYSTEM_PROMPT, "meta": SUN_TZU_METADATA},
    "nikola_tesla": {"prompt": TESLA_SYSTEM_PROMPT, "meta": TESLA_METADATA},
    "cleopatra": {"prompt": CLEOPATRA_SYSTEM_PROMPT, "meta": CLEOPATRA_METADATA},
    "machiavelli": {"prompt": MACHIAVELLI_SYSTEM_PROMPT, "meta": MACHIAVELLI_METADATA},
    # Board 2
    "ada_lovelace": {"prompt": ADA_LOVELACE_SYSTEM_PROMPT, "meta": ADA_LOVELACE_METADATA},
    "alan_turing": {"prompt": ALAN_TURING_SYSTEM_PROMPT, "meta": ALAN_TURING_METADATA},
    "grace_hopper": {"prompt": GRACE_HOPPER_SYSTEM_PROMPT, "meta": GRACE_HOPPER_METADATA},
    "linus_torvalds": {"prompt": LINUS_TORVALDS_SYSTEM_PROMPT, "meta": LINUS_TORVALDS_METADATA},
    "margaret_hamilton": {"prompt": MARGARET_HAMILTON_SYSTEM_PROMPT, "meta": MARGARET_HAMILTON_METADATA},
    "hedy_lamarr": {"prompt": HEDY_LAMARR_SYSTEM_PROMPT, "meta": HEDY_LAMARR_METADATA},
    # Board 3
    "steve_jobs": {"prompt": STEVE_JOBS_SYSTEM_PROMPT, "meta": STEVE_JOBS_METADATA},
    "niki_lauda": {"prompt": NIKI_LAUDA_SYSTEM_PROMPT, "meta": NIKI_LAUDA_METADATA},
    "marie_curie": {"prompt": MARIE_CURIE_SYSTEM_PROMPT, "meta": MARIE_CURIE_METADATA},
    "walt_disney": {"prompt": WALT_DISNEY_SYSTEM_PROMPT, "meta": WALT_DISNEY_METADATA},
    "frida_kahlo": {"prompt": FRIDA_KAHLO_SYSTEM_PROMPT, "meta": FRIDA_KAHLO_METADATA},
    "sherlock_holmes": {"prompt": SHERLOCK_HOLMES_SYSTEM_PROMPT, "meta": SHERLOCK_HOLMES_METADATA},
}

BOARDS = {
    "historical_thinkers": [
        "socrates", "leonardo_da_vinci", "sun_tzu",
        "nikola_tesla", "cleopatra", "machiavelli"
    ],
    "technical_experts": [
        "ada_lovelace", "alan_turing", "grace_hopper",
        "linus_torvalds", "margaret_hamilton", "hedy_lamarr"
    ],
    "market_audience": [
        "steve_jobs", "niki_lauda", "marie_curie",
        "walt_disney", "frida_kahlo", "sherlock_holmes"
    ],
}


def get_persona(persona_id: str) -> dict:
    """Get a persona's system prompt and metadata by ID."""
    if persona_id not in PERSONA_REGISTRY:
        raise ValueError(f"Unknown persona: {persona_id}. Available: {list(PERSONA_REGISTRY.keys())}")
    return PERSONA_REGISTRY[persona_id]


def get_board(board_name: str) -> list[dict]:
    """Get all personas in a board."""
    if board_name not in BOARDS:
        raise ValueError(f"Unknown board: {board_name}. Available: {list(BOARDS.keys())}")
    return [PERSONA_REGISTRY[pid] for pid in BOARDS[board_name]]


def get_all_personas() -> dict:
    """Get the complete persona registry."""
    return PERSONA_REGISTRY
