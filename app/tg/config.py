import os


class Configuration:
    def __init__(self):
        token = os.getenv("TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not token or not telegram_chat_id:
            raise ValueError("Missing TOKEN or TELEGRAM_CHAT_ID in environment")

        self._token: str = token
        self._telegram_chat_id: int = int(telegram_chat_id)

    def get_token(self):
        return self._token

    def get_chat_id(self):
        return self._telegram_chat_id
