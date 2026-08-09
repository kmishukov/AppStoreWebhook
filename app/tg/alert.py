import asyncio
import logging

import telegram

from app.tg.config import Configuration

logger = logging.getLogger(__name__)


def _handle_send_result(task: asyncio.Task) -> None:
    """Retrieve background delivery errors without logging sensitive URLs."""
    try:
        task.result()
    except asyncio.CancelledError:
        logger.warning("Telegram message delivery was cancelled")
    except Exception as error:  # noqa: BLE001 - third-party task may raise any error
        logger.error("Telegram message delivery failed (%s)", type(error).__name__)


def send_message(message: str) -> None:
    """
    Send a message to Telegram.

    Args:
        message: Message text to send
    """
    config = Configuration()
    bot = telegram.Bot(config.get_token())

    loop = asyncio.get_event_loop()
    task = loop.create_task(
        bot.send_message(text=message, chat_id=config.get_chat_id(), parse_mode="HTML")
    )
    task.add_done_callback(_handle_send_result)
