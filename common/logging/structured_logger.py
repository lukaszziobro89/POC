import logging
from http import HTTPStatus
from typing import Optional

from .schemas import AuditLogFormat, AUDIT_LOG_LEVEL_NUM, DomainLogFormat


class StructuredLogger(logging.Logger):
    def audit(
            self,
            event: str,
            base_url: str,
            client: str,
            client_ip_address: str,
            http_method: str,
            path: str,
            status_code: int,
            request_id: Optional[str] = None,
            **kwargs
    ):
        if self.isEnabledFor(AUDIT_LOG_LEVEL_NUM):
            log_entry = AuditLogFormat(
                event=event,
                base_url=base_url,
                client=client,
                client_ip_address=client_ip_address,
                http_method=http_method,
                path=path,
                status_code=HTTPStatus(status_code),
                request_id=request_id,
                **kwargs
            )
            self._log(AUDIT_LOG_LEVEL_NUM, log_entry.model_dump_json(exclude_none=True), ())


    def _validate_domain_log_format(
            self,
            log_level: int,
            event: str,
            request_id: str,
            document_id: Optional[str] = None,
            **kwargs
    ):
        if self.isEnabledFor(log_level):
            log_entry = DomainLogFormat(event=event, request_id=request_id, document_id=document_id, **kwargs)
            self._log(log_level, log_entry.model_dump_json(exclude_none=True), ())

    def info(
            self,
            event: str,
            request_id: Optional[str] = None,
            document_id: Optional[str] = None,
            **kwargs
    ):
        self._validate_domain_log_format(
            log_level=logging.INFO,
            event=event,
            request_id=request_id,
            document_id=document_id,
            **kwargs
        )

    def debug(
            self,
            event: str,
            request_id: Optional[str] = None,
            document_id: Optional[str] = None,
            **kwargs
    ):
        self._validate_domain_log_format(
            log_level=logging.DEBUG,
            event=event,
            request_id=request_id,
            document_id=document_id,
            **kwargs
        )

    def warning(
            self,
            event: str,
            request_id: Optional[str] = None,
            document_id: Optional[str] = None,
            **kwargs
    ):
        self._validate_domain_log_format(
            log_level=logging.WARNING,
            event=event,
            request_id=request_id,
            document_id=document_id,
            **kwargs
        )

    def error(
            self,
            event: str,
            request_id: Optional[str] = None,
            document_id: Optional[str] = None,
            **kwargs
    ):
        self._validate_domain_log_format(
            log_level=logging.ERROR,
            event=event,
            request_id=request_id,
            document_id=document_id,
            **kwargs
        )
