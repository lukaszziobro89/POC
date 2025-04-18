from typing import Any
import uuid

from structured_logger import StructuredLogger

class GenerateEventIdProcessor:
    def __call__(self, logger: StructuredLogger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        if "event_id" not in event_dict:
            event_dict["event_id"] = uuid.uuid4()
        return event_dict