# Shared constants used across multiple services.
# Centralizes terpene/cannabinoid mappings, classification thresholds,
# and strain name normalization data to prevent duplication.

# ---------------------------------------------------------------------------
# Terpene field mapping: source API/CSV field names -> standard internal names
# Used by cannlytics_client.py and init_datasets.py parsers
# ---------------------------------------------------------------------------

TERPENE_FIELD_MAP = {
    'beta_myrcene': 'myrcene',
    'myrcene': 'myrcene',
    'd_limonene': 'limonene',
    'limonene': 'limonene',
    'beta_caryophyllene': 'caryophyllene',
    'caryophyllene': 'caryophyllene',
    'alpha_pinene': 'alpha_pinene',
    'beta_pinene': 'beta_pinene',
    'terpinolene': 'terpinolene',
    'humulene': 'humulene',
    'alpha_humulene': 'humulene',
    'linalool': 'linalool',
    'ocimene': 'ocimene',
    'beta_ocimene': 'ocimene',
    'alpha_bisabolol': 'bisabolol',
    'bisabolol': 'bisabolol',
    'camphene': 'camphene',
    'geraniol': 'geraniol',
    'nerolidol': 'nerolidol',
    'alpha_terpinene': 'alpha_terpinene',
    'gamma_terpinene': 'gamma_terpinene',
    'caryophyllene_oxide': 'caryophyllene_oxide',
}

# ---------------------------------------------------------------------------
# Cannabinoid field mapping: source API/CSV field names -> standard internal names
# Used by cannlytics_client.py and init_datasets.py parsers
# ---------------------------------------------------------------------------

CANNABINOID_FIELD_MAP = {
    'thc': 'thc',
    'delta_9_thc': 'thc',
    'total_thc': 'thc',
    'thca': 'thca',
    'thcv': 'thcv',
    'cbd': 'cbd',
    'total_cbd': 'cbd',
    'cbda': 'cbda',
    'cbdv': 'cbdv',
    'cbn': 'cbn',
    'cbg': 'cbg',
    'cbga': 'cbg',
    'cbgm': 'cbgm',
    'cbgv': 'cbgv',
    'cbc': 'cbc',
    'cbcv': 'cbcv',
    'cbv': 'cbv',
    'cbe': 'cbe',
    'cbt': 'cbt',
    'cbl': 'cbl',
    'total_terpenes': 'total_terpenes',
}

# ---------------------------------------------------------------------------
# Classification thresholds (used by classifier.py)
# ---------------------------------------------------------------------------

ORANGE_THRESHOLD = 0.35      # Terpinolene >= this → ORANGE
GREEN_THRESHOLD = 0.35       # Combined pinene >= this → GREEN
BLUE_THRESHOLD = 0.35        # Myrcene >= this → BLUE
PURPLE_CARYOPHYLLENE_MIN = 0.30  # Caryophyllene >= this for PURPLE
PURPLE_PINENE_MAX = 0.15     # Pinene <= this for PURPLE
YELLOW_THRESHOLD = 0.30      # Limonene >= this → YELLOW
RED_BALANCED_MIN = 0.20      # Each of myrcene/limonene/caryophyllene >= this for RED
RED_PINENE_MAX = 0.15        # Pinene <= this for RED
RED_HUMULENE_MAX = 0.15      # Humulene <= this for RED

# Fallback threshold for dominance detection via top-terpene comparison
DOMINANCE_MARGIN = 0.10

# ---------------------------------------------------------------------------
# Data completeness thresholds (used by analyzer.py)
# ---------------------------------------------------------------------------

MIN_TERPENES_FOR_COMPLETE = 5

# ---------------------------------------------------------------------------
# Strain name normalization suffixes
# Shared between analyzer.py and profile_cache.py
# ---------------------------------------------------------------------------

STRAIN_NAME_SUFFIXES = [
    'flower', 'bud', 'strain', 'cannabis',
    'indica', 'sativa', 'hybrid',
    'concentrate', 'extract', 'rosin',
]
