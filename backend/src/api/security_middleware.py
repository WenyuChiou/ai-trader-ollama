"""
Security middleware for API authentication
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import os
from typing import Optional


class AdminSecretAuth:
    """Admin API Key authentication"""
    
    def __init__(self):
        self.admin_secret = os.getenv("ADMIN_SECRET")
        self.environment = os.getenv("ENVIRONMENT", "development")
    
    def verify(self, request: Request) -> bool:
        """
        Verify admin secret from request headers
        
        Checks:
        1. x-admin-secret header
        2. Authorization: Bearer <token> header
        
        Returns True if valid, False otherwise
        """
        # Skip authentication in development mode if ADMIN_SECRET is not set
        if self.environment == "development" and not self.admin_secret:
            return True
        
        # If ADMIN_SECRET is set, require authentication even in development
        if not self.admin_secret:
            return False
        
        # Check x-admin-secret header
        admin_secret_header = request.headers.get("x-admin-secret")
        if admin_secret_header == self.admin_secret:
            return True
        
        # Check Authorization: Bearer token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()
            if token == self.admin_secret:
                return True
        
        return False


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to protect sensitive endpoints with admin authentication"""
    
    # Protected endpoints (POST methods only)
    PROTECTED_PATHS = [
        "/api/trading/execute-trade",
        "/api/trading/check-pending-orders",
        "/api/system/init",
        "/api/portfolio/record-equity",
    ]
    
    def __init__(self, app):
        super().__init__(app)
        self.auth = AdminSecretAuth()
    
    async def dispatch(self, request: Request, call_next):
        # Only check POST requests to protected paths
        if request.method == "POST" and any(request.url.path.startswith(path) for path in self.PROTECTED_PATHS):
            if not self.auth.verify(request):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "ok": False,
                        "error": "Unauthorized: Admin secret required",
                        "message": "This endpoint requires admin authentication. Provide x-admin-secret header or Authorization: Bearer <token>"
                    }
                )
        
        response = await call_next(request)
        return response

