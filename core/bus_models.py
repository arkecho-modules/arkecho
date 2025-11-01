# core/bus_models.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class BusMessage:
    """
    Standardized message on the ArkEcho bus.
    """
    event: str
    data: Dict[str, Any]

@dataclass
class ModuleContext:
    """
    Context object passed between modules (could be extended as needed).
    """
    context: Dict[str, Any]
