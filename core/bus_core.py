# core/bus_core.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
# Event bus core for inter-module communication

from core.bus_models import BusMessage

class Bus:
    """
    Simple publish-subscribe event bus. Modules can publish events
    and subscribe callbacks to handle events.
    """
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type: str, callback):
        """
        Register a callback for a specific event_type.
        """
        self.subscribers.setdefault(event_type, []).append(callback)

    def publish(self, event_type: str, data: dict):
        """
        Publish an event to all subscribers of that event_type.
        """
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(BusMessage(event=event_type, data=data))
                except Exception:
                    continue
