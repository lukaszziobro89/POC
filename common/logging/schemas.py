from enum import Enum
from http import HTTPStatus
from typing import Optional, Literal
import uuid

from pydantic import BaseModel, ConfigDict


AUDIT_LOG_LEVEL_NUM = 60
AUDIT_LOG_LEVEL_NAME = "AUDIT"

class LogType(str, Enum):
    AUDIT = "AUDIT"
    DOMAIN = "DOMAIN"

class LogsExtraFields(str, Enum):
    ENABLED = "1"
    DISABLED = "0"

class LogFormat(BaseModel):
    datetime: str
    event: str
    event_id: uuid.UUID
    filename: str
    func_name: str
    level: str
    lineno: int
    log_type: LogType
    module: str
    request_id: str

    model_config = ConfigDict(extra="allow" if LogsExtraFields.DISABLED == LogsExtraFields.ENABLED else "ignore")

class DomainLogFormat(LogFormat):
    document_id: Optional[str] = None
    log_type: Literal[LogType.DOMAIN] = LogType.DOMAIN

class AuditLogFormat(LogFormat):
    base_url: str
    client: str
    client_ip_address: str
    http_method: str
    log_type: Literal[LogType.AUDIT] = LogType.AUDIT
    path: str
    status_code: HTTPStatus