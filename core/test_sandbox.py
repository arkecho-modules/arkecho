# Hard sandbox: block common I/O in tests
import builtins, sys
def _blocked(*a, **k): raise PermissionError("I/O blocked in test sandbox")
builtins.open = _blocked  # block file writes/reads in tests
sys.modules['requests'] = None  # block HTTP clients if someone imports them
