"""Opt-in Telegram HTML widget delivery with legacy text fallback."""

import asyncio
import logging
import os

import httpx

from app.tg.alert import send_message
from app.tg.config import Configuration
from app.tg.widget import render_notification_widget

logger = logging.getLogger(__name__)
MODES = frozenset({"text", "widget"})


def get_message_mode() -> str:
    mode = (os.getenv("TELEGRAM_MESSAGE_MODE") or "text").strip().lower()
    if mode not in MODES:
        raise ValueError("TELEGRAM_MESSAGE_MODE must be 'text' or 'widget'")
    return mode


async def _send_widget_with_fallback(message: str, html: str) -> None:
    config = Configuration()
    url = f"https://api.telegram.org/bot{config.get_token()}/sendWidget"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": config.get_chat_id(),
                    "html": html,
                    "caption": "App Store notification",
                    "allow_queries": False,
                },
            )
            response.raise_for_status()
            if response.json().get("ok") is not True:
                raise ValueError("Telegram rejected widget request")
    except Exception as exc:  # noqa: BLE001 — any failed widget send falls back to text
        # Never log the URL, error body or token-bearing exception text.
        logger.warning("Widget delivery failed (%s); sending text", type(exc).__name__)
        send_message(message)


def send_notification(message: str, payload: dict) -> None:
    """Send legacy text by default; widget mode degrades to text on failure."""
    if get_message_mode() == "text":
        send_message(message)
        return

    try:
        widget_html = render_notification_widget(payload)
    except Exception as exc:  # noqa: BLE001 — preserve notification delivery
        logger.warning("Widget rendering failed (%s); sending text", type(exc).__name__)
        send_message(message)
        return

    task = asyncio.get_running_loop().create_task(
        _send_widget_with_fallback(message, widget_html)
    )

    def report_error(result: asyncio.Task) -> None:
        try:
            result.result()
        except asyncio.CancelledError:
            logger.warning("Widget delivery task cancelled")
        except Exception as exc:  # noqa: BLE001
            logger.error("Widget delivery task failed (%s)", type(exc).__name__)

    task.add_done_callback(report_error)
