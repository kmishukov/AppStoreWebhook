import requests
from app.tg.config import Configuration

def send_message(message: str) -> None:
    """
    Send a message to Telegram.
    
    Args:
        message: Message text to send
    """
    config = Configuration()
    url = f"https://api.telegram.org/bot{config.getToken()}/sendMessage"
    
    response = requests.post(
        url,
        json={
            "chat_id": config.getAdminID(),
            "text": message,
            "parse_mode": "HTML"
        }
    )
    response.raise_for_status()