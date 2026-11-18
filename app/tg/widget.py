"""A compact static HTML widget for verified App Store events."""

import html
import zlib
from datetime import datetime
from typing import Any

from app.message_formatter import format_timestamp

MAX_HTML_BYTES = 32768
MAX_COMPRESSED_BYTES = 4096


def _safe(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_notification_widget(payload: dict[str, Any]) -> str:
    """Render a self-contained widget without remote resources or executable JS."""
    data = payload.get("data")
    identity = data if isinstance(data, dict) else {}
    kind = str(payload.get("notificationType") or "UNKNOWN")
    subtype = payload.get("subtype")
    bundle = identity.get("bundleId") or "Unknown app"
    environment = identity.get("environment") or "Unknown"
    uuid = payload.get("notificationUUID") or "N/A"
    signed_date = payload.get("signedDate")
    timestamp = format_timestamp(signed_date) if isinstance(signed_date, int) else "N/A"

    # Keep transaction IDs and signed payloads out of the widget.
    details = [
        ("App", bundle),
        ("Environment", environment),
        ("Date", timestamp),
        ("Notification ID", uuid),
    ]
    rows = "".join(
        '<div class="row"><span class="muted">' + _safe(label) +
        '</span><span class="value">' + _safe(value) + '</span></div>'
        for label, value in details
    )
    subtitle = (
        '<div class="subtitle">' + _safe(subtype) + '</div>' if subtype else ""
    )
    markup = (
        '<!doctype html><html><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>'
        '*{box-sizing:border-box}body{margin:0;padding:16px;'
        'font-family:-apple-system,BlinkMacSystemFont,sans-serif;'
        'color:var(--tg-theme-text-color,#202124);'
        'background:var(--tg-theme-bg-color,#fff)}'
        '.eyebrow{font-size:11px;font-weight:600;letter-spacing:1px;'
        'text-transform:uppercase;opacity:.65}'
        'h2{font-size:19px;line-height:1.2;margin:8px 0;font-weight:700;'
        'overflow-wrap:anywhere}.subtitle{font-size:12px;margin-bottom:12px;'
        'opacity:.7}.row{display:flex;justify-content:space-between;gap:10px;'
        'padding:9px 0;border-top:1px solid rgba(120,120,120,.2);'
        'font-size:12px}.muted{opacity:.65;flex-shrink:0}'
        '.value{text-align:right;overflow-wrap:anywhere;min-width:0}'
        '</style></head><body>'
        '<div class="eyebrow">App Store Event</div>'
        '<h2>' + _safe(kind) + '</h2>' + subtitle + rows +
        '</body></html>'
    )
    raw = markup.encode("utf-8")
    if len(raw) > MAX_HTML_BYTES or len(zlib.compress(raw, level=9)) > MAX_COMPRESSED_BYTES:
        raise ValueError("Telegram widget exceeds HTML size limits")
    return markup
