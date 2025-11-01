# core/loader.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
# Dynamic loader for core (similar to bus loader)

import importlib

_modules_cache_core = {}

def load_module(path: str):
    """
    Dynamically import a module attribute given its full dotted path and cache it.
    """
    if path in _modules_cache_core:
        return _modules_cache_core[path]
    if "." not in path:
        raise ValueError(f"Invalid module path: {path}")
    mod_name, attr = path.rsplit(".", 1)
    module = importlib.import_module(mod_name)
    func = getattr(module, attr)
    _modules_cache_core[path] = func
    return func
