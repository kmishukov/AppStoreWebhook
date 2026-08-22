import os


class Configuration:
    def __init__(self):
        token = (os.getenv("TOKEN") or "").strip()
        telegram_chat_id = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()

        if not token:
            raise ValueError("Missing TOKEN in environment")
        if not telegram_chat_id:
            raise ValueError("Missing TELEGRAM_CHAT_ID in environment")

        self._token: str = token
        try:
            self._telegram_chat_id: int = int(telegram_chat_id)
        except ValueError as exc:
            raise ValueError("TELEGRAM_CHAT_ID must be an integer") from exc

    def get_token(self):
        return self._token

    def get_chat_id(self):
        return self._telegram_chat_id


def validate_telegram_configuration() -> None:
    """Fail fast during startup when Telegram configuration is invalid."""
    Configuration()
