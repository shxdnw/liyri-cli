import os
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "mode": "focus",
    "minimal": False,
    "player": "",
    "speed": 1.0,
    "no_sync": False,
    "strip_keywords": True,
    "sticky_player": True
}

_VALIDATORS = {
    "mode": lambda v: v in ("focus", "scroll"),
    "speed": lambda v: isinstance(v, (int, float)) and 0.1 <= v <= 10.0,
}

def get_config_path():
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if not config_home:
        config_home = os.path.join(os.path.expanduser("~"), ".config")
    
    config_dir = os.path.join(config_home, "liyri")
    return os.path.join(config_dir, "config.json")

def load_config():
    config_path = Path(get_config_path())
    
    if not config_path.exists():
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        except Exception:
            pass
        return DEFAULT_CONFIG.copy()
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            
            cfg = DEFAULT_CONFIG.copy()
            for k, v in user_config.items():
                if k in cfg and type(v) == type(cfg[k]):
                    if k in _VALIDATORS and not _VALIDATORS[k](v):
                        continue
                    cfg[k] = v
            return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()
