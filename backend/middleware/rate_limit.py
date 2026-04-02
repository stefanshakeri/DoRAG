import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.redis import redis_client

logger = logging.getLogger("dorag")

# rate limit rules per route prefix
RATE_LIMIT_RULES = {
    "/chatbots/chat":       {"limit": 20, "window": 60},
    "/chatbots/documents":  {"limit": 10, "window": 60},
    "/chatbots":            {"limit": 60, "window": 60},
    "/users":               {"limit": 60, "window": 60},
    "/auth":                {"limit": 10, "window": 60}
}

DEFAULT_RULE = {"limit": 60, "window": 60}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # skip rate limiting for docs/health check
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/health"]:
            return await call_next(request)
        
        # get user ID (else IP)
        user_id = get_user_id(request)

        # find matching rule
        rule = get_rule(request.url.path)
        limit = rule["limit"]
        window = rule["window"]

        # check, increment request count
        redis_key = f"ratelimit:{user_id}:{request.url.path}"

        try:
            count = await redis_client.incr(redis_key)
            if count == 1:
                await redis_client.expire(redis_key, window)
            
            remaining = max(0, limit - count)

            if count > limit:
                logger.warning(
                    f"Rate limit exceeded: user={user_id} "
                    f"path={request.url.path} "
                    f"count={count}/{limit}"
                )
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded. Try again in {window} seconds."},
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Window": str(window),
                        "Retry-After": str(window)
                    }
                )
            
            response = await call_next(request)

            # attach rate limit info into response headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Window"] = str(window)

            return response
        
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)} - failing open")
            return await call_next(request)