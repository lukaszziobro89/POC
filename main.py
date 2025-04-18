from http import HTTPStatus

from fastapi import FastAPI, Request
from structlog import getLogger
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

from common.logging.structured_logger import StructuredLogger

app = FastAPI()

logger = StructuredLogger("PNC_LOGGER")


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())

        # Log audit information before processing the request
        logger.audit(
            event="Incoming request",
            path=request.url.path,
            base_url=str(request.url),
            client=request.headers.get("user-agent", "unknown"),
            client_ip_address=request.client.host,
            http_method=request.method,
            status_code=HTTPStatus.NO_CONTENT,  # Status code will be logged after the response
            request_id=request_id,
        )

        # Process the request
        response = await call_next(request)

        # Log audit information after processing the request
        logger.audit(
            event="Outgoing request",
            path=request.url.path,
            base_url=str(request.url),
            client=request.headers.get("user-agent", "unknown"),
            client_ip_address=request.client.host,
            http_method=request.method,
            status_code=response.status_code,
            request_id=request_id,
        )

        return response

# Add the middleware to the app
app.add_middleware(AuditLoggingMiddleware) # type: ignore


@app.get("/")
async def root():
    # logger.info("ASDF")
    return {"message": "Hello World"}


@app.get("/r2")
async def root2():
    # logger.info("r2")
    return {"message": "r2"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}