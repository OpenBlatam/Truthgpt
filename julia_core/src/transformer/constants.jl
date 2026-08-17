"""
Transformer Constants

Default architectural configurations, initialization scales, and generation defaults.
"""

# Default configuration values
const DEFAULT_D_MODEL = 768
const DEFAULT_N_HEADS = 12
const DEFAULT_N_LAYERS = 12
const DEFAULT_D_FF = 3072
const DEFAULT_VOCAB_SIZE = 32000
const DEFAULT_MAX_SEQ_LEN = 2048
const DEFAULT_DROPOUT = 0.1f0
const DEFAULT_LAYER_NORM_EPS = 1f-5
const DEFAULT_ROPE_BASE = 10000.0f0

# Weight initialization
const DEFAULT_EMBED_SCALE = 0.02f0
const DEFAULT_LM_HEAD_SCALE = 0.02f0

# Generation defaults
const DEFAULT_MAX_NEW_TOKENS = 100
const DEFAULT_TEMPERATURE = 1.0f0
const DEFAULT_TOP_K = 50
const DEFAULT_TOP_P = 0.9f0
const DEFAULT_EOS_TOKEN_ID = 2
