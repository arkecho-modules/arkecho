# bus/loader.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
# Dynamic module loader with caching for ArkEcho bus

import importlib

_modules_cache = {}

def load_module(path: str):
    """
    Dynamically import a module attribute given its full dotted path and cache it.
    Example path: "modules.module_name.run"
    """
    if path in _modules_cache:
        return _modules_cache[path]
    if "." not in path:
        raise ValueError(f"Invalid module path: {path}")
    mod_name, attr = path.rsplit(".", 1)
    module = importlib.import_module(mod_name)
    func = getattr(module, attr)
    _modules_cache[path] = func
    return func
