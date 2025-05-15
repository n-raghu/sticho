"""
Authentication middleware for Stytch OAuth.

This module contains all authentication-related functionality:
1. StytchAuthMiddleware - Validates requests before they reach endpoints
2. setup_auth_routes - Adds authentication routes to the FastAPI app
3. require_auth - Dependency for requiring authentication in FastAPI routes
"""

from typing import Any, Callable, Dict, Optional, List, Annotated

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header, Cookie
from service.cfg import cfg
from stytch import Client
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

# Create Stytch client using configuration from cfg.py
stytch_client = Client(
    project_id=cfg.project_id,
    secret=cfg.secret,
    environment=cfg.env
)

# List of paths that don't require authentication
PUBLIC_PATHS = [
    "/",
    "/auth/",
    "/auth/sso/google",
    "/auth/callback",
    "/docs",
    "/redoc",
]


class StytchAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.public_paths = PUBLIC_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not cfg.enforce_iam:
            print("AUTH MIDDLEWARE: IAM enforcement is disabled, bypassing authentication")
            request.state.authenticated = True
            return await call_next(request)
        if any(request.url.path.startswith(path) for path in self.public_paths):
            return await call_next(request)

        if request.url.path.startswith("/gql"):
            print(f"AUTH MIDDLEWARE: GraphQL request detected: {request.url.path}")

            session_token = request.cookies.get("session")
            if not session_token and "Authorization" in request.headers:
                auth_header = request.headers["Authorization"]
                if auth_header.startswith("Bearer "):
                    session_token = auth_header[7:]
            session_token = session_token.strip()
            print(f"AUTH MIDDLEWARE: Session token: {session_token}")

            if not session_token:
                print("AUTH MIDDLEWARE: No session token found, returning 401")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Authentication required for GraphQL endpoint"}
                )

            # Validate the session token
            try:
                print(f"AUTH MIDDLEWARE: Validating session token: {session_token[:10]}...")
                session = await validate_session(session_token)
                print(f"AUTH MIDDLEWARE: Session validated successfully for user: {session.get('user_id')}")

                # Store session info in request state for the endpoint to use
                request.state.session = session
                request.state.authenticated = True
                request.state.user_id = session.get("user_id")

                # Continue to the endpoint
                print("AUTH MIDDLEWARE: Continuing to GraphQL endpoint")
                return await call_next(request)
            except Exception as e:
                print(f"AUTH MIDDLEWARE: Session validation failed: {str(e)}")
                return JSONResponse(
                    status_code=401,
                    content={"error": f"Invalid session: {str(e)}"}
                )

        # For non-GraphQL endpoints that aren't in the public paths list
        # Check for session token in cookies or Authorization header
        session_token = request.cookies.get("session")
        if not session_token and "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                session_token = auth_header[7:]  # Remove 'Bearer ' prefix

        if not session_token:
            return JSONResponse(
                status_code=401,
                content={"error": "Authentication required"}
            )

        # Validate the session token
        try:
            session = await validate_session(session_token)
            # Store session info in request state for the endpoint to use
            request.state.session = session
            request.state.authenticated = True
            request.state.user_id = session.get("user_id")

            # Continue to the endpoint
            return await call_next(request)
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"error": f"Invalid session: {str(e)}"}
            )


async def validate_session(session_token: str) -> Dict[str, Any]:
    """
    Validate a session token.

    Args:
        session_token: JWT session token

    Returns:
        Dict: Session information including user_id

    Raises:
        Exception: If session is invalid
    """
    if not session_token:
        print("VALIDATE SESSION: No session token provided")
        raise Exception("No session token provided")

    try:
        print(f"VALIDATE SESSION: Attempting to validate token: {session_token}")

        # Use local JWT validation first for performance
        session = stytch_client.sessions.authenticate_jwt_local(
            session_jwt=session_token
        )

        if not session:
            print("VALIDATE SESSION: Local validation failed, trying API validation")
            # Fall back to API validation if local validation fails
            result = stytch_client.sessions.authenticate(
                session_jwt=session_token
            )
            print(f"VALIDATE SESSION: API validation successful for user: {result.user_id}")
            return {
                "user_id": result.user_id,
                "session_id": result.session_id,
                "authenticated": True
            }

        print(f"VALIDATE SESSION: Local validation successful for user: {session.user_id}")
        return {
            "user_id": session.user_id,
            "session_id": session.session_id,
            "authenticated": True
        }
    except Exception as e:
        print(f"VALIDATE SESSION: Validation failed with error: {str(e)}")
        raise Exception(f"Invalid session: {str(e)}")


async def start_google_oauth() -> RedirectResponse:
    """
    Start the Google OAuth flow.

    Returns:
        RedirectResponse: Redirect to Google OAuth page
    """
    # Get the Google OAuth URL
    oauth_url = f"https://{cfg.env}.stytch.com/v1/public/oauth/google/start"

    # Build the full URL with parameters
    full_url = f"{oauth_url}?public_token={cfg.public_token}&login_redirect_url={cfg.redirect_url}"

    # Redirect to the OAuth URL
    return RedirectResponse(url=full_url)


async def handle_oauth_callback(token: Optional[str] = None) -> Response:
    """
    Handle the OAuth callback.

    Args:
        token: Authentication token from OAuth provider

    Returns:
        Response: Redirect with session cookie or error response
    """
    if not token:
        return JSONResponse(
            status_code=400,
            content={"error": "No authentication token provided"}
        )

    try:
        # Authenticate with the token
        result = stytch_client.oauth.authenticate(token=token)

        # Create a response that redirects to the GraphQL endpoint
        response = RedirectResponse(url="/gql")

        # Set the session cookie
        response.set_cookie(
            key="session",
            value=result.session_jwt,
            httponly=True,
            samesite="lax"
        )

        return response
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"error": f"Authentication failed: {str(e)}"}
        )


async def require_auth(
    request: Request,
    session: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Dependency for requiring authentication in FastAPI routes.

    Args:
        request: The request object
        session: Session cookie
        authorization: Authorization header

    Returns:
        Dict: Session information

    Raises:
        HTTPException: If authentication fails
    """
    print("REQUIRE_AUTH: Checking authentication")

    # Check if IAM enforcement is disabled
    if not cfg.enforce_iam:
        print("REQUIRE_AUTH: IAM enforcement is disabled, bypassing authentication")
        # Return a dummy session
        dummy_session = {
            "user_id": "anonymous",
            "session_id": "none",
            "authenticated": True
        }
        # Store session info in request state
        request.state.session = dummy_session
        request.state.authenticated = True
        request.state.user_id = "anonymous"
        return dummy_session

    # Get session token from cookie or header
    session_token = session
    if not session_token and authorization:
        if authorization.startswith("Bearer "):
            session_token = authorization[7:]  # Remove 'Bearer ' prefix
        else:
            session_token = authorization
        session_token = session_token.strip()

    if not session_token:
        print("REQUIRE_AUTH: No session token found")
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    try:
        # Validate the session token
        print(f"REQUIRE_AUTH: Validating session token: {session_token}")
        session_info = await validate_session(session_token)
        print(f"REQUIRE_AUTH: Session info: {session_info}")
        print(f"REQUIRE_AUTH: Session validated for user: {session_info.get('user_id')}")

        # Store session info in request state
        request.state.session = session_info
        request.state.authenticated = True
        request.state.user_id = session_info.get("user_id")

        return session_info
    except Exception as e:
        print(f"REQUIRE_AUTH: Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid session: {str(e)}"
        )


def setup_auth_routes(app: FastAPI) -> None:
    """
    Set up authentication routes for the FastAPI app.

    Args:
        app: FastAPI application
    """
    @app.get("/auth/sso/google")
    async def google_sso_route():
        """Start Google SSO flow."""
        return await start_google_oauth()

    @app.get("/auth/callback")
    async def callback_route(token: str = None):
        """Handle OAuth callback."""
        print("Token:", token)
        return await handle_oauth_callback(token)
