import asyncio

import telegram

from app.tg.config import Configuration


def send_message(message: str) -> None:
    """
    Send a message to Telegram.

    Args:
        message: Message text to send
    """
    config = Configuration()
    bot = telegram.Bot(config.get_token())

    loop = asyncio.get_event_loop()
    loop.create_task(
        bot.send_message(text=message, chat_id=config.get_chat_id(), parse_mode="HTML")
    )
