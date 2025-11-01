# core/contract.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
from dataclasses import dataclass
from typing import Literal, Dict, Any

@dataclass
class ModuleOutput:
    """
    Standardized module output for ArkEcho pipeline modules.
    """
    ok: bool = True
    action: Literal["allow", "ask", "block", "defer"] = "allow"
    risk: Literal["low", "med", "high", "vhigh"] = "low"
    rationale: str = ""
    data: Dict[str, Any] = None

def coerce_output(output) -> ModuleOutput:
    """
    Normalize various types of outputs into a ModuleOutput object.
    Handles ModuleOutput instances, dicts, or raw values.
    """
    if isinstance(output, ModuleOutput):
        return output

    # Set defaults
    ok = True
    action = "allow"
    risk = "low"
    rationale = ""
    data = {}

    # If module returned a dict
    if isinstance(output, dict):
        ok = output.get("ok", True)
        action = output.get("action", "allow")
        risk_val = output.get("risk", "low")
        rationale = output.get("rationale", "")
        data = output.get("data", {})

        # Convert numeric risk to label
        if isinstance(risk_val, (int, float)):
            x = risk_val
            if x <= 0.2:
                risk = "low"
            elif x <= 0.5:
                risk = "med"
            elif x <= 0.8:
                risk = "high"
            else:
                risk = "vhigh"
        else:
            risk = str(risk_val) if risk_val is not None else "low"

    else:
        # If output is None
        if output is None:
            return ModuleOutput(ok=True, action="allow", risk="low", rationale="", data={})
        # If output is boolean
        elif isinstance(output, bool):
            ok = output
            action = "allow" if output else "block"
        # If output is numeric
        elif isinstance(output, (int, float)):
            ok = True
            x = float(output)
            if x <= 0.2:
                risk = "low"
            elif x <= 0.5:
                risk = "med"
            elif x <= 0.8:
                risk = "high"
            else:
                risk = "vhigh"
        else:
            # Other types: place in rationale
            rationale = str(output)

    return ModuleOutput(ok=ok, action=action, risk=risk, rationale=rationale, data=data)
