import asyncio

import telegram
from app.tg.config import Configuration

async def send_message_async(message: str) -> None:
    """
    Send a message to Telegram.
    
    Args:
        message: Message text to send
    """
    config = Configuration()
    bot = telegram.Bot(config.getToken())
    async with bot:
        await bot.send_message(
            text=message,
            chat_id=config.getAdminID(),
            parse_mode="HTML"
        )

def send_message(message: str) -> None:
    """
    Synchronous wrapper for sending Telegram message.
    
    Args:
        message: Message text to send
    """
    asyncio.run(send_message_async(message))