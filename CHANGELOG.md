# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `LICENSE` (MIT).
- CI workflow (GitHub Actions) running lint (`ruff`, `isort`) and the test suite on push/PR.
- Test suite (`pytest`) covering JWT validation and the webhook endpoint.
- `pyproject.toml` with project metadata and packaging config.
- Community files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue/PR templates.
- Trusted JWS verification using Apple's official App Store Server Library and Apple Root CA G3.
- Multi-app verification with per-app verifier caching and an optional bundle ID/App Apple ID allowlist.
- Environment selection and optional OCSP certificate revocation checks.
- Privacy-safe notification metadata logging and Telegram HTML escaping.
- Telegram HTTP request log suppression to prevent bot token disclosure.
- Configurable message timezone.
- Smaller Docker build context, non-root container user, and Docker build CI check.
- Automated versioned Docker image publishing to GitHub Container Registry.

## [1.0.0]

### Added

- FastAPI service receiving App Store Server Notifications V2.
- JWT signature validation (ES256) using the leaf certificate from the `x5c` header.
- Telegram alerts for subscription and purchase lifecycle events.
- Docker Compose setup with a health-check endpoint.
