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

- `ADMIN_ID` is the destination Telegram chat ID.
- `TOKEN` is the bot token issued by [BotFather](https://t.me/BotFather).

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

## Security note

The current validator verifies an ES256 signature using the leaf certificate from the JWT `x5c` header, but does not validate the full certificate chain against a trusted Apple Root CA. Add certificate-chain validation before using the service in production.

## Documentation

- [App Store Server Notifications](https://developer.apple.com/documentation/appstoreservernotifications)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PyJWT](https://pyjwt.readthedocs.io/)

## License

This project is licensed under the [MIT License](LICENSE).
