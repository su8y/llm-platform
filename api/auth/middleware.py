# CORS Settings - Dynamic origin handling for credentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        origin = request.headers.get("origin")

        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
                # Get actual requested headers or use common ones
                requested_headers = request.headers.get("access-control-request-headers", "")
                if requested_headers:
                    response.headers["Access-Control-Allow-Headers"] = requested_headers
                else:
                    response.headers["Access-Control-Allow-Headers"] = "authorization, content-type, accept, origin, user-agent"
                response.headers["Access-Control-Expose-Headers"] = "id"
                response.headers["Access-Control-Max-Age"] = "3600"
            return response

        # Handle actual requests
        response = await call_next(request)
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "id"

        return response