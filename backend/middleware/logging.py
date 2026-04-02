import time
import uuid
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("dorag")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # generate unique request ID for tracing
        request_id = str(uuid.uuid4())[:8]

        # log the incoming request
        logger.info(f"[{request_id}] --> {request.method} {request.url.path}")

        # time the request
        start = time.time()
        try:
            response = await call_next(request)
            duration = (time.time() - start) * 1000

            # log the request
            logger.info(
                f"[{request_id}] <-- {response.status_code} "
                f"{request.method} {request.url.path} "
                f"({duration:.2f} ms)"
            )

            return response

        except Exception as e:
            logger.error(f"[{request_id}] <-- ERR {request.method} {request.url.path} (Error: {str(e)})")
            raise