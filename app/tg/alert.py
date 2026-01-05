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
    bot = telegram.Bot(config.getToken())

    loop = asyncio.get_event_loop()
    loop.run(bot.send_message(text=message, chat_id=config.getAdminID(), parse_mode="HTML"))
    # async def _send():
    #     async with bot:
    #         await bot.send_message(
    #             text=message,
    #             chat_id=config.getAdminID(),
    #             parse_mode="HTML"
    #         )
    
    # asyncio.run(_send())