# core/helpers/thresholds.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
"""
Central registry for global risk and policy thresholds.
Loads values from configs/thresholds.yaml or uses safe defaults.
"""
import os

# Default threshold values
DEFAULTS = {
    "ask": 0.45,       # Trigger "ask" threshold
    "block": 0.70,     # Trigger "block" threshold
    "drift": 0.25,     # Alignment drift tolerance
    "media_theta": 0.65,  # Bulk media risk threshold
    "quorum": 3        # Consensus quorum count
}

# Loaded thresholds (populated at import)
THRESHOLDS = DEFAULTS.copy()

# Attempt to load from configs/thresholds.yaml
config_path = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "configs", "thresholds.yaml")
if os.path.isfile(config_path):
    try:
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    try:
                        val_num = float(val)
                        THRESHOLDS[key] = val_num
                    except ValueError:
                        THRESHOLDS[key] = val
    except Exception:
        THRESHOLDS = DEFAULTS.copy()
