# Security Policy

## Overview

This document outlines the security measures, best practices, and vulnerability reporting procedures for the Claude Plays Zelda project.

## Table of Contents

1. [Supported Versions](#supported-versions)
2. [Security Features](#security-features)
3. [Security Best Practices](#security-best-practices)
4. [Configuration Security](#configuration-security)
5. [Web Dashboard Security](#web-dashboard-security)
6. [API Security](#api-security)
7. [Reporting Vulnerabilities](#reporting-vulnerabilities)
8. [Security Updates](#security-updates)

---

## Supported Versions

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| 1.x.x   | :white_check_mark: | Active           |
| < 1.0   | :x:                | No longer supported |

---

## Security Features

### Authentication

The project implements token-based authentication for API access:

- **API Key Authentication**: Required for protected endpoints
- **Multiple Authentication Methods**: Header, query parameter, or custom header
- **Configurable**: Can be disabled for development (not recommended for production)

### Rate Limiting

Protection against abuse through rate limiting:

- **Per-minute limits**: Default 60 requests/minute per IP
- **Per-hour limits**: Default 1000 requests/hour per IP
- **Configurable thresholds**: Adjustable based on needs
- **Automatic cleanup**: Old rate limit data is automatically purged

### CORS Protection

Cross-Origin Resource Sharing (CORS) protection:

- **Environment-based**: Strict in production, permissive in development
- **Allowlist-based**: Only specified origins allowed in production
- **Configurable**: Custom origin lists supported

### Secure Defaults

- **Secret key generation**: Automatic secure random key generation
- **HTTPS-ready**: Designed to work behind reverse proxy with TLS
- **Input validation**: All inputs validated before processing
- **Path sanitization**: File paths validated to prevent directory traversal

---

## Security Best Practices

### 1. API Keys and Secrets

**DO**:
- Store API keys in environment variables
- Use `.env` file for local development (never commit it)
- Rotate API keys regularly
- Use different keys for different environments

**DON'T**:
- Never hardcode API keys in source code
- Never commit `.env` files to version control
- Never share API keys in public channels
- Never use production keys in development

Example `.env` file:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
FLASK_SECRET_KEY=your-secure-random-key
TWITCH_OAUTH_TOKEN=oauth:your-token-here
API_KEYS=key1,key2,key3  # Comma-separated list
```

### 2. Network Security

**Production Deployment**:
```yaml
# Use reverse proxy (nginx, Apache)
# with TLS termination

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Docker Security

When using Docker:

```dockerfile
# Don't run as root
USER nonroot

# Use specific versions
FROM python:3.11-slim

# Don't expose unnecessary ports
EXPOSE 5000

# Use secrets for sensitive data
# Mount secrets at runtime, don't bake into image
```

### 4. Configuration Security

**Secure configuration example**:
```python
from claude_plays_zelda.web.server import WebServer

server = WebServer(
    host="0.0.0.0",  # Bind to all interfaces
    port=5000,
    config={
        "environment": "production",  # Enable strict mode
        "api_keys": os.environ.get("API_KEYS", "").split(","),
        "allowed_origins": [
            "https://yourdomain.com",
            "https://www.yourdomain.com"
        ],
        "secret_key": os.environ.get("FLASK_SECRET_KEY"),
        "rate_limit_per_minute": 30,  # Strict limit
        "rate_limit_per_hour": 500,
    }
)
```

---

## Configuration Security

### Environment Variables

Required environment variables for secure operation:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...        # Claude API key

# Recommended
FLASK_SECRET_KEY=...                # Flask session encryption
API_KEYS=key1,key2,key3             # API authentication keys

# Optional (for streaming)
TWITCH_OAUTH_TOKEN=oauth:...        # Twitch integration
TWITCH_CHANNEL=your_channel         # Twitch channel name
```

### Configuration Validation

The project includes comprehensive configuration validation:

```python
from claude_plays_zelda.core.validators import ConfigValidators

# Validate API key format
ConfigValidators.validate_api_key(
    key=api_key,
    key_name="Anthropic API Key"
)

# Validate paths to prevent directory traversal
ConfigValidators.validate_path(
    path=user_provided_path,
    must_exist=True
)

# Validate network ports
ConfigValidators.validate_port(port=5000)
```

---

## Web Dashboard Security

### Authentication Setup

Enable authentication for web dashboard:

```python
# Generate API keys
from claude_plays_zelda.web.security import generate_api_key

api_key = generate_api_key()
print(f"New API key: {api_key}")
# Store this securely!
```

### Client Authentication

JavaScript client example:

```javascript
// Using Authorization header (recommended)
fetch('/api/state', {
    headers: {
        'Authorization': `Bearer ${apiKey}`
    }
});

// Using X-API-Key header
fetch('/api/state', {
    headers: {
        'X-API-Key': apiKey
    }
});
```

### WebSocket Security

WebSocket connections inherit authentication from HTTP:

```javascript
const socket = io({
    auth: {
        token: apiKey
    }
});
```

---

## API Security

### Rate Limiting

Respect rate limits in API clients:

```python
import time
from requests.exceptions import HTTPError

def make_api_request(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        if e.response.status_code == 429:
            # Rate limited - back off
            retry_after = int(e.response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            return make_api_request(url, headers)  # Retry
        raise
```

### Input Validation

All API inputs are validated:

```python
from claude_plays_zelda.web.security import validate_input

data = request.get_json()
is_valid, error = validate_input(
    data,
    required_fields=["action", "parameters"]
)

if not is_valid:
    return jsonify({"error": error}), 400
```

---

## Reporting Vulnerabilities

### How to Report

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. **DO** report via [GitHub Security Advisories](https://github.com/clduab11/claude-plays-zelda/security/advisories)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

### Disclosure Policy

- Coordinated disclosure preferred
- 90-day disclosure deadline
- Credit given to reporters (if desired)
- Security advisories published after fix

---

## Security Updates

### Severity Levels

- **Critical**: Immediate update required
  - Remote code execution
  - Authentication bypass
  - Data breach potential

- **High**: Update within 7 days
  - Privilege escalation
  - Sensitive data exposure
  - DOS vulnerabilities

- **Medium**: Update within 30 days
  - Information disclosure
  - CSRF vulnerabilities
  - Missing input validation

- **Low**: Update when convenient
  - Minor information leaks
  - UI-only vulnerabilities
  - Theoretical issues

### Update Process

1. Monitor GitHub releases and security advisories
2. Review CHANGELOG.md for security fixes
3. Test updates in staging environment
4. Deploy to production
5. Verify security fix

### Automated Updates

Consider using Dependabot or similar tools:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

---

## Security Checklist

### Pre-Deployment

- [ ] All API keys stored in environment variables
- [ ] `.env` file in `.gitignore`
- [ ] HTTPS/TLS enabled
- [ ] Authentication enabled for production
- [ ] CORS configured for production domains
- [ ] Rate limiting configured
- [ ] Logging enabled and monitored
- [ ] Dependencies up to date
- [ ] Security scan completed

### Production Monitoring

- [ ] Monitor rate limit violations
- [ ] Monitor authentication failures
- [ ] Review access logs regularly
- [ ] Set up alerts for suspicious activity
- [ ] Keep dependencies updated
- [ ] Regular security audits
- [ ] Backup sensitive data
- [ ] Incident response plan in place

---

## Security Contacts

- **Security Issues**: [GitHub Security Advisories](https://github.com/clduab11/claude-plays-zelda/security/advisories)
- **Project Maintainers**: [See CONTRIBUTING.md]
- **General Issues**: [GitHub Issues](https://github.com/clduab11/claude-plays-zelda/issues)

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [Python Security Guidelines](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)

---

## License

This security policy is part of the Claude Plays Zelda project and is licensed under the same terms as the project (GNU AGPL-3.0).

---

**Last Updated**: November 20, 2025
**Version**: 1.0.0
