# App Store Webhook Handler

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

A small FastAPI service for receiving App Store Server Notifications V2 and forwarding subscription event alerts to Telegram.

## Features

- Validates signed JWT payloads from App Store notifications
- Handles common subscription and purchase events
- Sends formatted alerts to Telegram
- Supports unknown notification types
- Includes Docker Compose and a health-check endpoint

## Quick start

Clone the repository and create an environment file:

```bash
git clone https://github.com/kmishukov/AppStoreWebhook.git
cd AppStoreWebhook
cp .env.example .env
```

Add your Telegram credentials to `.env`:

- `TELEGRAM_CHAT_ID` is the destination Telegram chat ID.
- `TOKEN` is the bot token issued by [BotFather](https://t.me/BotFather).

Configure Apple verification:

- `APPLE_ENVIRONMENTS` controls whether the service accepts `Production`, `Sandbox`, or both.
- `APPLE_ENABLE_ONLINE_CHECKS` enables Apple certificate revocation checks through OCSP.
- `APPLE_ROOT_CA_PATHS` optionally overrides the bundled root certificate with one or more certificate paths separated by `:`.
- `APPLE_ALLOWED_APPS` is an optional JSON object mapping bundle IDs to numeric Apple IDs.

By default, the service accepts notifications for any application when the complete
JWS certificate chain proves that Apple signed them. A verifier is created and cached
for every bundle ID and environment, so one webhook can serve multiple applications.
Set `APPLE_ALLOWED_APPS` only when you want to restrict the webhook to a known list:

```dotenv
APPLE_ALLOWED_APPS={"com.example.first":1234567890,"com.example.second":2345678901}
```

The repository includes Apple's public Root CA G3 certificate used to establish the
certificate chain. This certificate is public and is not an App Store Connect `.p8`
private key.

The service validates this configuration during startup and refuses to start when
required Apple settings or certificates are missing.

Start the service:

```bash
docker compose up --build -d
```

The API will be available at `http://localhost:8001`.

```bash
curl http://localhost:8001/health
```

## App Store Connect

Set your App Store Server Notifications URL to:

```text
https://your-domain.example/v1/webhook
```

The public endpoint must use HTTPS.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/v1/webhook` | App Store notification receiver |

## Development

Install dev dependencies and run the test suite:

```bash
pip install -r requirements-dev.txt
pytest
```

## Security

Signed notifications, transaction information, and renewal information are verified
with Apple's official App Store Server Library. Verification checks the certificate
chain against Apple Root CA G3 as well as the bundle ID, environment, and App Apple
ID contained in the Apple-signed payload. An optional allowlist can further restrict
which applications the webhook accepts.

## Documentation

- [App Store Server Notifications](https://developer.apple.com/documentation/appstoreservernotifications)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PyJWT](https://pyjwt.readthedocs.io/)

## License

This project is licensed under the [MIT License](LICENSE).
