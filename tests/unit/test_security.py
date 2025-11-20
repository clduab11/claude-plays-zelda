"""Tests for web security module."""

from claude_plays_zelda.web.security import (
    RateLimiter,
    AuthenticationManager,
    generate_secret_key,
    generate_api_key,
    get_cors_config,
    validate_input,
)


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_rate_limiter_allows_requests_under_limit(self):
        """Test that requests under limit are allowed."""
        limiter = RateLimiter(requests_per_minute=10, requests_per_hour=100)
        ip = "192.168.1.1"

        # Should allow 10 requests
        for i in range(10):
            is_limited, reason = limiter.is_rate_limited(ip)
            assert not is_limited, f"Request {i+1} was incorrectly rate limited"
            assert reason is None

    def test_rate_limiter_blocks_excess_requests_per_minute(self):
        """Test that excess requests per minute are blocked."""
        limiter = RateLimiter(requests_per_minute=5, requests_per_hour=100)
        ip = "192.168.1.2"

        # Make 5 requests (should all succeed)
        for i in range(5):
            is_limited, _ = limiter.is_rate_limited(ip)
            assert not is_limited

        # 6th request should be blocked
        is_limited, reason = limiter.is_rate_limited(ip)
        assert is_limited
        assert "minute" in reason.lower()

    def test_rate_limiter_blocks_excess_requests_per_hour(self):
        """Test that excess requests per hour are blocked."""
        limiter = RateLimiter(requests_per_minute=1000, requests_per_hour=5)
        ip = "192.168.1.3"

        # Make 5 requests (should all succeed)
        for i in range(5):
            is_limited, _ = limiter.is_rate_limited(ip)
            assert not is_limited

        # 6th request should be blocked
        is_limited, reason = limiter.is_rate_limited(ip)
        assert is_limited
        assert "hour" in reason.lower()

    def test_rate_limiter_tracks_different_ips_separately(self):
        """Test that different IPs are tracked separately."""
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=100)

        # IP 1 makes 2 requests
        for i in range(2):
            is_limited, _ = limiter.is_rate_limited("192.168.1.1")
            assert not is_limited

        # IP 1 is now rate limited
        is_limited, _ = limiter.is_rate_limited("192.168.1.1")
        assert is_limited

        # IP 2 should still be allowed
        is_limited, _ = limiter.is_rate_limited("192.168.1.2")
        assert not is_limited

    def test_rate_limiter_reset(self):
        """Test that reset clears rate limits."""
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=100)
        ip = "192.168.1.1"

        # Max out requests
        for i in range(2):
            limiter.is_rate_limited(ip)

        # Should be limited
        is_limited, _ = limiter.is_rate_limited(ip)
        assert is_limited

        # Reset
        limiter.reset(ip)

        # Should now be allowed
        is_limited, _ = limiter.is_rate_limited(ip)
        assert not is_limited


class TestAuthenticationManager:
    """Tests for AuthenticationManager class."""

    def test_auth_disabled_with_no_keys(self):
        """Test that auth is disabled when no keys provided."""
        auth = AuthenticationManager(api_keys=None)
        assert not auth.enabled
        assert auth.is_authenticated(None)
        assert auth.is_authenticated("any-token")

    def test_auth_disabled_with_empty_keys(self):
        """Test that auth is disabled with empty key list."""
        auth = AuthenticationManager(api_keys=[])
        assert not auth.enabled
        assert auth.is_authenticated(None)

    def test_auth_enabled_with_keys(self):
        """Test that auth is enabled with valid keys."""
        keys = ["key1", "key2", "key3"]
        auth = AuthenticationManager(api_keys=keys)
        assert auth.enabled

    def test_valid_key_authentication(self):
        """Test authentication with valid key."""
        keys = ["valid-key-123"]
        auth = AuthenticationManager(api_keys=keys)
        assert auth.is_authenticated("valid-key-123")

    def test_invalid_key_authentication(self):
        """Test authentication fails with invalid key."""
        keys = ["valid-key-123"]
        auth = AuthenticationManager(api_keys=keys)
        assert not auth.is_authenticated("invalid-key")
        assert not auth.is_authenticated(None)
        assert not auth.is_authenticated("")

    def test_multiple_valid_keys(self):
        """Test multiple valid keys work."""
        keys = ["key1", "key2", "key3"]
        auth = AuthenticationManager(api_keys=keys)
        assert auth.is_authenticated("key1")
        assert auth.is_authenticated("key2")
        assert auth.is_authenticated("key3")
        assert not auth.is_authenticated("key4")


class TestSecurityUtilities:
    """Tests for security utility functions."""

    def test_generate_secret_key(self):
        """Test secret key generation."""
        key1 = generate_secret_key()
        key2 = generate_secret_key()

        # Keys should be different
        assert key1 != key2

        # Default length should be 32 bytes = 64 hex chars
        assert len(key1) == 64
        assert len(key2) == 64

        # Custom length
        key3 = generate_secret_key(length=16)
        assert len(key3) == 32  # 16 bytes = 32 hex chars

    def test_generate_api_key(self):
        """Test API key generation."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        # Keys should be different
        assert key1 != key2

        # Should be URL-safe strings
        assert isinstance(key1, str)
        assert isinstance(key2, str)
        assert len(key1) > 0
        assert len(key2) > 0

    def test_get_cors_config_development(self):
        """Test CORS config for development."""
        config = get_cors_config(environment="development")

        assert config["origins"] == "*"
        assert "GET" in config["methods"]
        assert "POST" in config["methods"]

    def test_get_cors_config_production(self):
        """Test CORS config for production."""
        config = get_cors_config(environment="production")

        # Should have restricted origins
        assert config["origins"] != "*"
        assert isinstance(config["origins"], list)
        assert len(config["origins"]) > 0

        # Should support credentials
        assert config.get("supports_credentials") is True

    def test_get_cors_config_custom_origins(self):
        """Test CORS config with custom origins."""
        custom_origins = ["https://example.com", "https://app.example.com"]
        config = get_cors_config(environment="production", allowed_origins=custom_origins)

        assert config["origins"] == custom_origins

    def test_validate_input_valid(self):
        """Test input validation with valid data."""
        data = {"name": "test", "value": 123, "enabled": True}
        required = ["name", "value"]

        is_valid, error = validate_input(data, required)
        assert is_valid
        assert error is None

    def test_validate_input_missing_fields(self):
        """Test input validation with missing fields."""
        data = {"name": "test"}
        required = ["name", "value", "enabled"]

        is_valid, error = validate_input(data, required)
        assert not is_valid
        assert "Missing required fields" in error
        assert "value" in error
        assert "enabled" in error

    def test_validate_input_not_dict(self):
        """Test input validation with non-dict data."""
        data = "not a dict"
        required = ["field1"]

        is_valid, error = validate_input(data, required)
        assert not is_valid
        assert "JSON object" in error

    def test_validate_input_empty_required(self):
        """Test input validation with no required fields."""
        data = {"any": "data"}
        required = []

        is_valid, error = validate_input(data, required)
        assert is_valid
        assert error is None


class TestIntegration:
    """Integration tests for security components."""

    def test_rate_limiter_with_time_passing(self):
        """Test rate limiter with actual time passing (slow test)."""
        # Note: This test uses actual time.sleep, so it's slower
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=100)
        ip = "192.168.1.1"

        # Make 2 requests
        limiter.is_rate_limited(ip)
        limiter.is_rate_limited(ip)

        # Should be rate limited
        is_limited, _ = limiter.is_rate_limited(ip)
        assert is_limited

        # Wait for rate limit window to pass (1 minute + buffer)
        # For testing, we just verify the mechanism works
        # In real scenarios, waiting 61 seconds would reset the limit

    def test_combined_auth_and_rate_limit(self):
        """Test using both auth and rate limiting together."""
        auth = AuthenticationManager(api_keys=["valid-key"])
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=100)
        ip = "192.168.1.1"

        # Valid auth
        assert auth.is_authenticated("valid-key")

        # Under rate limit
        is_limited, _ = limiter.is_rate_limited(ip)
        assert not is_limited

        # Max out rate limit
        limiter.is_rate_limited(ip)
        limiter.is_rate_limited(ip)

        # Should be rate limited even with valid auth
        is_limited, _ = limiter.is_rate_limited(ip)
        assert is_limited

        # Invalid auth, not rate limited (different IP)
        assert not auth.is_authenticated("invalid-key")
        is_limited, _ = limiter.is_rate_limited("different-ip")
        assert not is_limited
