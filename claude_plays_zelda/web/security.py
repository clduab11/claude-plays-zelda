"""Security utilities for web server."""

import secrets
import time
from functools import wraps
from typing import Callable, Dict, Optional, List, Tuple
from collections import defaultdict
from flask import request, jsonify
from loguru import logger


class RateLimiter:
    """Rate limiter for API endpoints."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute per IP
            requests_per_hour: Maximum requests per hour per IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)

        logger.info(
            f"Rate limiter initialized: {requests_per_minute}/min, " f"{requests_per_hour}/hour"
        )

    def is_rate_limited(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """
        Check if IP address is rate limited.

        Args:
            ip_address: Client IP address

        Returns:
            Tuple of (is_limited, reason)
        """
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600

        # Clean old requests
        self.minute_requests[ip_address] = [
            t for t in self.minute_requests[ip_address] if t > minute_ago
        ]
        self.hour_requests[ip_address] = [t for t in self.hour_requests[ip_address] if t > hour_ago]

        # Remove IPs with no recent requests to prevent memory leak
        if not self.minute_requests[ip_address]:
            del self.minute_requests[ip_address]
        if not self.hour_requests[ip_address]:
            del self.hour_requests[ip_address]

        # Check minute limit
        if len(self.minute_requests.get(ip_address, [])) >= self.requests_per_minute:
            return True, "Rate limit exceeded: too many requests per minute"

        # Check hour limit
        if len(self.hour_requests.get(ip_address, [])) >= self.requests_per_hour:
            return True, "Rate limit exceeded: too many requests per hour"

        # Record request
        self.minute_requests[ip_address].append(now)
        self.hour_requests[ip_address].append(now)

        return False, None

    def reset(self, ip_address: Optional[str] = None):
        """
        Reset rate limits.

        Args:
            ip_address: Optional IP to reset, if None resets all
        """
        if ip_address:
            self.minute_requests.pop(ip_address, None)
            self.hour_requests.pop(ip_address, None)
        else:
            self.minute_requests.clear()
            self.hour_requests.clear()


class AuthenticationManager:
    """Simple token-based authentication manager."""

    def __init__(self, api_keys: Optional[List[str]] = None):
        """
        Initialize authentication manager.

        Args:
            api_keys: List of valid API keys. If None, auth is disabled.
        """
        self.api_keys = set(api_keys) if api_keys else None
        self.enabled = api_keys is not None and len(api_keys) > 0

        if self.enabled:
            logger.info(f"Authentication enabled with {len(self.api_keys)} valid keys")
        else:
            logger.warning("Authentication is DISABLED - use only for development!")

    def is_authenticated(self, token: Optional[str]) -> bool:
        """
        Check if token is valid.

        Args:
            token: API token to validate

        Returns:
            True if authenticated or auth is disabled
        """
        if not self.enabled:
            return True

        return token in self.api_keys

    def get_token_from_request(self) -> Optional[str]:
        """
        Extract authentication token from request.

        Returns:
            Token string or None
        """
        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]

        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key

        # Check query parameter
        return request.args.get("api_key")


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a secure random secret key.

    Args:
        length: Length of key in bytes

    Returns:
        Hex-encoded secret key
    """
    return secrets.token_hex(length)


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        URL-safe API key
    """
    return secrets.token_urlsafe(32)


def require_auth(auth_manager: AuthenticationManager):
    """
    Decorator to require authentication for routes.

    Args:
        auth_manager: AuthenticationManager instance

    Returns:
        Decorated function
    """

    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not auth_manager.enabled:
                return f(*args, **kwargs)

            token = auth_manager.get_token_from_request()

            if not auth_manager.is_authenticated(token):
                logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
                return jsonify({"error": "Unauthorized", "message": "Valid API key required"}), 401

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def apply_rate_limit(rate_limiter: RateLimiter):
    """
    Decorator to apply rate limiting to routes.

    Args:
        rate_limiter: RateLimiter instance

    Returns:
        Decorated function
    """

    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = request.remote_addr
            is_limited, reason = rate_limiter.is_rate_limited(ip_address)

            if is_limited:
                logger.warning(f"Rate limit exceeded for {ip_address}: {reason}")
                return jsonify({"error": "Rate limit exceeded", "message": reason}), 429

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_cors_config(
    environment: str = "production", allowed_origins: Optional[List[str]] = None
) -> Dict:
    """
    Get CORS configuration based on environment.

    Args:
        environment: Environment name (development, production)
        allowed_origins: List of allowed origins, if None uses defaults

    Returns:
        CORS configuration dictionary
    """
    if environment == "development":
        # Allow all origins in development
        return {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
        }

    # Production: restrictive CORS
    default_origins = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ]

    return {
        "origins": allowed_origins or default_origins,
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
        "supports_credentials": True,
    }


def validate_input(data: Dict, required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate input data has required fields.

    Args:
        data: Input data dictionary
        required_fields: List of required field names

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Input must be a JSON object"

    missing = [field for field in required_fields if field not in data]

    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    return True, None
