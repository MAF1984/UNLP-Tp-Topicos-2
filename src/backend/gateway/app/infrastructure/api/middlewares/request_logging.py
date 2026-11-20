import json
import logging
import sys
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Logger estructurado a stdout
logger = logging.getLogger("gateway.access")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware transversal de observabilidad (ADR 005):
    1. Inicia temporizador de alta precisión (perf_counter).
    2. Extrae o genera Correlation-ID (X-Request-ID).
    3. Inyecta identificador en la respuesta.
    4. Emite bitácora JSON estructurada con duración en milisegundos.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        # Extraer o generar X-Request-ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            log_record = {
                "timestamp": time.time(),
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "error": str(e)
            }
            logger.error(json.dumps(log_record))
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(round(duration_ms, 2))

        log_record = {
            "timestamp": time.time(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2)
        }
        logger.info(json.dumps(log_record))

        return response
