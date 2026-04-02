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
        
        # global rate limit check
        if await self.check_global_limit(request.url.path):
            return JSONResponse(
                status_code=503,
                content={"detail": "Service is temporarily overloaded. Please try again later."}
            )
        
        # get user ID (else IP)
        user_id = self.get_user_id(request)

        # find matching rule
        rule = self.get_rule(request.url.path)
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
        
    async def check_global_limit(path: str) -> bool:
        '''
        If global limit is exceeded, returns true

        :param path: Request path as string
        :returns: True if global limit exceeded, else False
        '''
        global_rules = {
            "/chatbots/chat": {"limit": 1000, "window": 60},
            "/chatbots/documents": {"limit": 200, "window": 60}
        }

        for prefix, rule in global_rules.items():
            if prefix in path:
                key = f"global_ratelimit:{prefix}"
                count = await redis_client.incr(key)
                if count == 1:
                    await redis_client.expire(key, rule["window"])
                if count > rule["limit"]:
                    return True
        
        return False
    
    @staticmethod
    def get_user_id(request: Request) -> str:
        '''
        Extract user identifier from request. Uses auth token if present, falls back to IP address. 

        :param request: HTTP request object
        :returns: User identifier as string
        '''
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return f"user:{auth_header[-16:]}"
        
        # fall back to IP address otherwise
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"

        return f"ip:{request.client.host if request.client else 'unknown'}"
    
    @staticmethod
    def get_rule(path: str) -> dict:
        '''
        Find the most specific matching rule for a given path. 

        :param path: Request path as string
        :returns: Matching rate limit rule as dictionary
        '''
        for prefix, rule in RATE_LIMIT_RULES.items():
            if prefix in path:
                return rule

        return DEFAULT_RULE