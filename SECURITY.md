# Security Guidelines

This document outlines security considerations and best practices for the Prema Review Intelligence application.

## Environment Variables and Secrets Management

- **Never commit `.env` files** to version control. The `.env` file is already in `.gitignore`.
- Always use `.env.example` as a template for configuration.
- Use environment variables or a secrets management service (e.g., AWS Secrets Manager, HashiCorp Vault) for production deployments.
- Rotate API keys regularly, especially if they are exposed or suspected to be compromised.

## File Upload Security

### Current Protections

1. **File Type Validation**: Only `.csv`, `.json`, and `.ndjson` files are accepted.
2. **File Size Limits**: Maximum upload size is configurable via `MAX_UPLOAD_SIZE` (default: 10MB).
3. **Row Limit Protection**: Maximum rows processed per file is configurable via `MAX_INGESTION_ROWS` (default: 50,000) to prevent DoS attacks.
4. **Input Validation**: JSON parsing includes error handling and size limits.
5. **Content Sanitization**: Text normalization is applied to review content.

### Recommendations

- Monitor file upload patterns for abuse.
- Consider implementing virus scanning for uploaded files in production.
- Add rate limiting per IP address for file uploads.
- Log all file upload attempts for security auditing.

## CORS Configuration

- **Development**: CORS allows all origins (`*`) for local development.
- **Production**: Must configure `CORS_ALLOWED_ORIGINS` with a comma-separated list of allowed origins.
- Never use wildcard (`*`) in production when `allow_credentials=True`.
- Regularly review and update the list of allowed origins.

## Database Security

### SQLite (Development)

- SQLite is suitable for development but **not recommended for production**.
- File-based database can be vulnerable to:
  - File system attacks
  - Concurrent write issues
  - Limited scalability

### Production Recommendations

1. **Use PostgreSQL or MySQL** for production deployments.
2. **Connection Pooling**: Configured to prevent connection exhaustion.
3. **Connection Timeouts**: Set to prevent hanging connections.
4. **Use Connection String Environment Variables**: Never hardcode database credentials.
5. **Enable SSL/TLS**: Use encrypted connections for database access.
6. **Regular Backups**: Implement automated backup strategies.
7. **Access Control**: Limit database access to application servers only.

### Database URL Format

- **SQLite**: `sqlite:///./data/app.db`
- **PostgreSQL**: `postgresql://user:password@host:port/database`
- **MySQL**: `mysql://user:password@host:port/database`

## LLM API Security

### API Key Management

- API keys are validated on client creation.
- Keys are stored in environment variables, never in code.
- Keys are validated for proper format before use.

### Rate Limiting

- Rate limiting is implemented to prevent API abuse and cost overruns.
- Default: 60 requests per minute (configurable via `LLM_RATE_LIMIT_RPM`).
- Monitor API usage and adjust limits based on your provider's quotas.

### Recommendations

- Set up billing alerts with your LLM provider.
- Monitor API usage patterns for anomalies.
- Use separate API keys for development and production.
- Implement per-user rate limiting if multi-tenant.

## Input Validation

### Current Protections

- File uploads are validated for type and size.
- JSON parsing includes error handling.
- Text normalization sanitizes input.
- SQL injection protection via SQLModel/SQLAlchemy ORM.

### Additional Recommendations

- Implement request timeout limits.
- Add input length validation for form fields.
- Sanitize all user-generated content before storage.
- Use parameterized queries (handled by ORM).

## Authentication and Authorization

**Current Status**: Not implemented. The API is currently open.

### Recommendations for Production

1. **Implement Authentication**: Use JWT tokens or OAuth2.
2. **API Key Authentication**: For programmatic access.
3. **Role-Based Access Control (RBAC)**: Different permissions for different users.
4. **Rate Limiting**: Per-user/per-IP rate limits.
5. **Audit Logging**: Log all API access and modifications.

## Dependency Security

### Regular Audits

- Regularly run `poetry audit` or use tools like `safety` to check for vulnerabilities.
- Keep dependencies up to date.
- Review changelogs before upgrading major versions.
- Subscribe to security advisories for your dependencies.

### Tools for Security Audits

```bash
# Check for known vulnerabilities
poetry audit

# Or use safety (requires installation)
pip install safety
safety check
```

## Logging and Monitoring

### Current Implementation

- Structured logging is configured via `app.core.logging`.
- Log level is configurable via `LOG_LEVEL`.

### Recommendations

- **Log Sensitive Operations**: File uploads, API key usage, database changes.
- **Monitor for Anomalies**: Unusual request patterns, failed authentications, errors.
- **Alert on Security Events**: Failed login attempts, rate limit violations, suspicious uploads.
- **Avoid Logging Secrets**: Never log API keys, passwords, or tokens.

## Production Deployment Checklist

- [ ] Replace SQLite with PostgreSQL/MySQL
- [ ] Configure `CORS_ALLOWED_ORIGINS` for production
- [ ] Set strong, unique API keys for LLM providers
- [ ] Enable HTTPS/TLS for all connections
- [ ] Implement authentication and authorization
- [ ] Configure proper firewall rules
- [ ] Set up automated backups
- [ ] Enable security monitoring and alerting
- [ ] Review and configure rate limiting
- [ ] Set up log aggregation and monitoring
- [ ] Run security audits on dependencies
- [ ] Configure environment-specific settings

## Security Incident Response

1. **Identify**: Detect and confirm the security issue.
2. **Contain**: Limit the impact (revoke keys, disable features, etc.).
3. **Eradicate**: Remove the threat (patch vulnerabilities, update dependencies).
4. **Recover**: Restore services with security fixes.
5. **Review**: Post-mortem analysis and improvements.

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:
1. Do not create public issues for security vulnerabilities.
2. Contact the maintainers directly.
3. Provide detailed information about the vulnerability.
4. Allow time for the issue to be addressed before public disclosure.

