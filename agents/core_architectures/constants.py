# Leak Re-creation: constants.ts equivalent
# Reconstructed directly from the Claude Code source map leak

# Internal Anthropic Model Codenames (Leaked)
# These are used to unlock specific API routing behaviors in the QueryEngine
MODEL_CODENAMES = {
    "claude-code": "Tengu",         # The CLI tool itself and its virtual pet
    "opus-4.6": "Fennec",           # Unreleased high-reasoning model
    "next-gen-family": "Capybara",  # New model family internal reference
}

# Feature Flags (Leaked from constants.ts)
FEATURE_FLAGS = {
    "ENABLE_ULTRAPLAN": True,       # Long-horizon 30-minute thinking mode (CCR)
    "ENABLE_TENGU_BUDDY": True,     # Tamagotchi-style productivity tracking
    "ENABLE_GHOST_MODE": False,     # Similar to Undercover Mode but for network routing
    "ENABLE_SAP_BAML": True,        # Schema-Aligned Parsing for robust prompt compilation
}

# System API Constraints
MAX_BUDGET_USD_DEFAULT = 1.00       # --max-budget-usd default CLI argument
ULTRAPLAN_MAX_ITERATIONS = 50       # Extended recursive loop limit for Fennec/UltraPlan

def get_feature_flag(flag_name: str) -> bool:
    return FEATURE_FLAGS.get(flag_name, False)
