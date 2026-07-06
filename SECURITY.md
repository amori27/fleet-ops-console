# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of fleet-ops-console seriously. If you discover a security vulnerability, please report it responsibly.

**Do not open a public issue.** Instead, send a private report to the maintainer at **amir@example.com**.

Please include the following details:

- A description of the vulnerability
- Steps to reproduce
- Affected versions
- Any potential mitigations you have identified

You can expect:

- **Acknowledgment** within 48 hours of your report
- **An initial assessment** within 5 business days
- **Regular updates** on the progress toward a fix
- **Credit** for the discovery (if you wish) once the issue is resolved

We will coordinate disclosure with you and will not release details publicly until a fix is available and deployed.

## Best Practices

- **Never** commit secrets, API keys, or passwords to the repository
- Use environment variables for all sensitive configuration
- Rotate `FLEET_JWT_SECRET` regularly in production deployments
- Keep dependencies up to date to avoid known CVEs
