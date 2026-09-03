# 25_SECURITY.md

## Security

This document defines security practices for the PREDIXA AI system.

## API Key Protection

- All API keys stored in environment variables, never in code
- Use .env files locally (in .gitignore)
- Production: HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault
- Keys rotated every 90 days
- Different keys per environment (dev/staging/prod)

## Environment Variables

`ash
# Required environment variables
DATABASE_URL=postgresql://user:pass@host:5432/predixa
REDIS_URL=redis://host:6379/0
MLFLOW_TRACKING_URI=http://mlflow:5000
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=xxx
S3_SECRET_KEY=xxx
API_KEY_SECRET=xxx  # For signing JWTs
EXTERNAL_API_KEYS=xxx,yyy  # Data provider keys
`

## Secrets Management

| Secret | Storage | Rotation |
|--------|---------|----------|
| Database password | Vault/Secrets Manager | 90 days |
| Redis password | Vault/Secrets Manager | 90 days |
| S3 credentials | Vault/Secrets Manager | 90 days |
| External API keys | Vault/Secrets Manager | Per provider |
| JWT signing key | Vault/Secrets Manager | 180 days |
| MLflow backend | Vault/Secrets Manager | 90 days |

## Authentication

- API Key authentication for programmatic access
- JWT tokens for dashboard users
- API keys: 32-char random strings, hashed in DB (bcrypt)
- JWT: RS256, 15-min access, 7-day refresh
- Rate limiting per API key

## Input Validation

- Pydantic models for all request bodies
- Strict type validation
- String length limits
- SQL injection prevention via parameterized queries
- XSS prevention via output encoding

## Rate Limiting

`python
# Per API key
DEFAULT_LIMIT = 1000  # requests per minute
BURST_LIMIT = 200
`

## Logging Policy

- Never log: API keys, passwords, PII, full credit cards
- Log: Request IDs, timestamps, endpoints, status codes, latency
- Structured JSON logging for SIEM integration
- Correlation IDs across services

## Network Security

- VPC isolation for all services
- Private subnets for databases
- Public subnets only for load balancers
- Security groups: least privilege
- TLS 1.3 everywhere (internal + external)
- mTLS for service-to-service

## Data Protection

- Encryption at rest: AES-256 (database, S3)
- Encryption in transit: TLS 1.3
- PII minimization: Only store what's needed
- Data retention policies enforced
- Right to deletion implemented

## Vulnerability Management

- Dependabot/Renovate for dependency updates
- Weekly security scans (Trivy, Snyk)
- CVE monitoring for base images
- Patch critical within 48 hours

## Incident Response

1. Detect: Monitoring alerts
2. Contain: Revoke keys, isolate systems
3. Investigate: Logs, traces
4. Remediate: Patch, rotate, redeploy
5. Post-mortem: Document, improve
