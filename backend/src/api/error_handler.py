"""
Global error handler for FastAPI application.

Uses the standardized error envelope from Phase 4 (ADR-0003):
  {"ok": false, "error": {"code": str, "message": str, "details": any}, "request_id": str}
"""
import traceback
import uuid
import logging
from pathlib import Path
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def get_error_log_path() -> Path:
    """Get path to error log file"""
    backend_dir = Path(__file__).parent.parent.parent
    project_root = backend_dir.parent
    logs_dir = project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir / "api_errors.log"


def setup_error_logging():
    """Setup error logging configuration"""
    error_log_path = get_error_log_path()

    # Configure logging
    logging.basicConfig(
        filename=str(error_log_path),
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filemode='a'  # Append mode
    )

    return logging.getLogger(__name__)


def make_error_envelope(
    code: str,
    message: str,
    *,
    details: object = None,
    request_id: str | None = None,
) -> dict:
    """Build the standardized error envelope dict.

    Returns:
        {"ok": False, "error": {"code": ..., "message": ..., "details": ...}, "request_id": ...}
    """
    request_id = request_id or str(uuid.uuid4())[:8]
    envelope: dict = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
        "request_id": request_id,
    }
    if details is not None:
        envelope["error"]["details"] = details
    return envelope


def create_error_response(
    request: Request,
    exc: Exception,
    status_code: int = 500,
    custom_message: str = None
) -> JSONResponse:
    """
    Create standardized error response without exposing traceback.

    Uses the Phase 4 error envelope format.
    """
    request_id = str(uuid.uuid4())[:8]

    # Log full error details to file
    logger = setup_error_logging()
    logger.error(
        f"Request ID: {request_id}\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}\n"
        f"Error Type: {type(exc).__name__}\n"
        f"Error Message: {str(exc)}\n"
        f"Traceback:\n{traceback.format_exc()}"
    )

    # Determine error message
    if custom_message:
        error_message = custom_message
    elif status_code == 500:
        error_message = "Internal Server Error"
    else:
        error_message = str(exc) if str(exc) else "An error occurred"

    # Determine error code from exception type or status
    error_code = type(exc).__name__ if status_code != 500 else "internal_error"

    return JSONResponse(
        status_code=status_code,
        content=make_error_envelope(
            code=error_code,
            message=error_message,
            request_id=request_id,
        ),
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions"""
    return create_error_response(request, exc, status_code=500)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler for HTTP exceptions (4xx, etc.)"""
    request_id = str(uuid.uuid4())[:8]
    return JSONResponse(
        status_code=exc.status_code,
        content=make_error_envelope(
            code=f"http_{exc.status_code}",
            message=str(exc.detail) if exc.detail else "An error occurred",
            request_id=request_id,
        ),
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )
