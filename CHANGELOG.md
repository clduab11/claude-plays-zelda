# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - November 20, 2025

#### Security Enhancements
- **Authentication System** (`claude_plays_zelda/web/security.py`)
  - Token-based API authentication
  - Multiple authentication methods (Bearer, X-API-Key, query parameter)
  - Secure API key generation utilities
  - Configurable authentication (production/development modes)

- **Rate Limiting** (`claude_plays_zelda/web/security.py`)
  - Per-minute rate limits (default: 60 requests)
  - Per-hour rate limits (default: 1000 requests)
  - IP-based request tracking
  - Automatic cleanup of old request data
  - Configurable thresholds

- **CORS Protection** (`claude_plays_zelda/web/security.py`)
  - Environment-based CORS configuration
  - Strict production defaults with origin allowlist
  - Configurable allowed origins
  - Credential support for authenticated requests

- **Secure Secret Keys**
  - Automatic cryptographically secure key generation
  - Environment variable support
  - Warning logs for insecure configurations

#### Test Coverage
- **Security Module Tests** (`tests/unit/test_security.py`)
  - 30+ test cases for authentication and rate limiting
  - RateLimiter functionality tests
  - AuthenticationManager tests
  - Security utility function tests
  - CORS configuration tests
  - Input validation tests
  - Integration scenario tests

- **Vision Module Tests** (`tests/unit/test_vision.py`)
  - 25+ test cases for computer vision components
  - GameStateDetector tests
  - OCRProcessor tests
  - ObjectDetector tests
  - Vision pipeline integration tests
  - Multi-scale image handling tests

#### Performance Optimization
- **Vision Cache System** (`claude_plays_zelda/vision/cache.py`)
  - LRU cache with TTL support
  - Cache statistics tracking
  - Configurable cache size and expiration
  - Image-based cache key computation
  - Expected 40-60% CPU usage reduction during stable scenes

- **Image Comparator** (`claude_plays_zelda/vision/cache.py`)
  - Perceptual image hashing
  - Similarity detection between frames
  - Change detection for scene stability

- **Adaptive Vision Processor** (`claude_plays_zelda/vision/cache.py`)
  - Automatic frame rate adjustment
  - Scene change detection
  - Dynamic processing intervals (0.1s - 1.0s)
  - Responsive during changes, efficient during stability

#### Configuration Validation
- **Comprehensive Validators** (`claude_plays_zelda/core/validators.py`)
  - API key validation with placeholder detection
  - Path validation with existence/type checking
  - Network port validation
  - Numeric range validation
  - Model name validation
  - Log level validation
  - Time interval validation
  - Environment variable validation
  - Emulator configuration validation
  - Vision system validation
  - AI agent configuration validation

#### Documentation
- **API Documentation** (`docs/API.md`)
  - Complete API reference for all modules
  - Code examples for each component
  - Request/response formats
  - Error handling guidelines
  - Rate limiting information
  - Authentication methods
  - WebSocket event documentation
  - Best practices guide

- **Security Policy** (`SECURITY.md`)
  - Security features overview
  - Best practices for deployment
  - Configuration security guidelines
  - Vulnerability reporting procedures
  - Security update process
  - Pre-deployment checklist
  - Production monitoring guidelines

- **Improvements Documentation** (`docs/IMPROVEMENTS.md`)
  - Detailed changelog of all improvements
  - Migration guide for existing users
  - Performance metrics and expectations
  - Future recommendations
  - Testing results

### Changed - November 20, 2025

#### Web Server
- **Enhanced server.py** (`claude_plays_zelda/web/server.py`)
  - Integrated authentication system
  - Added rate limiting to API endpoints
  - Implemented environment-based CORS configuration
  - Secure secret key generation and management
  - Updated create_app() to return security components
  - Enhanced WebServer class initialization
  - Added security status to health check endpoint

### Security

#### Fixed
- **CORS Vulnerability**: Changed from allowing all origins (`*`) to restricted allowlist in production
- **Weak Secret Key**: Replaced hardcoded weak secret with cryptographically secure generation
- **No Authentication**: Added token-based authentication for API protection
- **No Rate Limiting**: Implemented rate limiting to prevent abuse
- **Input Validation**: Added comprehensive input validation across modules

#### Breaking Changes
- Web server initialization now requires security configuration for production use
- API endpoints now respect rate limits (may return 429 status)
- CORS restricted in production (may require origin configuration)
- create_app() now returns 4 values instead of 2 (backwards incompatible)

### Migration Notes

Users upgrading from previous versions should:

1. **Update Web Server Initialization**:
   ```python
   # Old
   server = WebServer(host="0.0.0.0", port=5000)

   # New (with security)
   server = WebServer(host="0.0.0.0", port=5000, config={
       "environment": "production",
       "api_keys": ["your-api-key"],
       "allowed_origins": ["https://yourdomain.com"]
   })
   ```

2. **Set Environment Variables**:
   ```bash
   FLASK_SECRET_KEY=your-secure-random-key
   API_KEYS=key1,key2,key3
   ```

3. **Update API Clients** to include authentication:
   ```python
   headers = {"Authorization": f"Bearer {api_key}"}
   ```

4. **Configure CORS** for production domains

See `docs/IMPROVEMENTS.md` for complete migration guide.

---

## [1.0.0] - 2025-XX-XX

### Initial Release
- AI agent for playing The Legend of Zelda
- Computer vision for game state detection
- Twitch streaming integration
- Web dashboard for monitoring
- Real-time decision making
- Memory and learning systems

---

## Notes

- All security improvements are backwards compatible when using development mode
- Production deployments should enable all security features
- Tests can be run with: `pytest tests/ -v`
- See `SECURITY.md` for security best practices
- See `docs/API.md` for complete API documentation
