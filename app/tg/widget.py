"""Old Navy-inspired HTML notification cards for Telegram widgets."""

import html
import zlib
from typing import Any

from app.jwt_validator import validate_transaction_token
from app.message_formatter import format_timestamp

MAX_HTML_BYTES = 32768
MAX_COMPRESSED_BYTES = 4096

# Display labels are deliberately separate from Apple's machine-readable event codes.
EVENTS = {
    "ONE_TIME_CHARGE": (
        "Purchase",
        "A one-time purchase or Family Sharing event",
        "↗",
        "purchase",
    ),
    "SUBSCRIBED": (
        "New subscription",
        "A subscription was started",
        "✦",
        "subscription",
    ),
    "DID_RENEW": (
        "Renewal",
        "A subscription renewed successfully",
        "↗",
        "subscription",
    ),
    "DID_FAIL_TO_RENEW": (
        "Billing issue",
        "A subscription renewal failed",
        "!",
        "refund",
    ),
    "REFUND": ("Refund", "A purchase was refunded", "↶", "refund"),
    "REFUND_DECLINED": (
        "Refund declined",
        "A refund request was declined",
        "↶",
        "refund",
    ),
    "REFUND_REVERSED": (
        "Refund reversed",
        "A refund was reversed",
        "↗",
        "purchase",
    ),
    "EXPIRED": (
        "Subscription expired",
        "A subscription has expired",
        "−",
        "refund",
    ),
    "REVOKE": (
        "Access revoked",
        "A purchase is no longer available",
        "−",
        "refund",
    ),
    "DID_CHANGE_RENEWAL_STATUS": (
        "Renewal settings",
        "Auto-renewal status changed",
        "↻",
        "subscription",
    ),
    "DID_CHANGE_RENEWAL_PREF": (
        "Plan changed",
        "Subscription renewal preferences changed",
        "↻",
        "subscription",
    ),
    "TEST": (
        "Test notification",
        "A test event from App Store Connect",
        "✓",
        "other",
    ),
}

_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:system-ui,sans-serif;color:#102d4e;background:#f7f9fd}
.hero{position:relative;overflow:hidden;padding:19px 19px 22px;color:#fff;
background:radial-gradient(circle at 100% 0%,#2a69a5 0%,transparent 53%),
linear-gradient(127deg,#061a36 0%,#003764 66%,#10518c 100%)}
.hero.subscription{background:radial-gradient(circle at 98% 4%,#3c78ac 0%,transparent 54%),
linear-gradient(127deg,#061b39,#123e70 75%,#28649d)}
.hero.refund{background:radial-gradient(circle at 96% 5%,#526f99 0%,transparent 52%),
linear-gradient(127deg,#0c1d36,#294466 75%,#365e86)}
.hero:before{content:"";position:absolute;right:-62px;bottom:-128px;width:280px;
height:280px;border:1px solid #ffffff38;border-radius:50%;
box-shadow:0 0 0 38px #ffffff0b,0 0 0 75px #ffffff08}
.hero>*{position:relative}
.top{display:flex;align-items:center;justify-content:space-between;gap:10px}
.brand{font-size:10px;font-weight:750;letter-spacing:1.45px}
.pill{border:1px solid #ffffff50;border-radius:50px;padding:5px 8px;
font-size:9px;letter-spacing:.65px;font-weight:700;color:#e6f3ff}
.heading{display:flex;align-items:center;justify-content:space-between;
gap:12px;margin-top:22px}
h1{font-size:30px;line-height:1.08;letter-spacing:-.85px;
font-weight:780;margin:0;overflow-wrap:anywhere}
.symbol{flex:none;display:flex;align-items:center;justify-content:center;
width:46px;height:46px;border-radius:50%;background:#ffffff1c;
border:1px solid #ffffff4d;font-size:24px}
.description{font-size:12px;line-height:1.45;margin:9px 0 0;color:#e5f0fc}
.content{background:#f7f9fd;padding:17px 19px 14px}
.app{display:flex;align-items:center;gap:11px;padding-bottom:15px}
.appmark{display:flex;align-items:center;justify-content:center;width:43px;
height:43px;border-radius:12px;background:#003764;color:#fff;
font-size:20px;font-weight:750;flex:none}
.appname{font-size:15px;font-weight:750;letter-spacing:-.25px;overflow-wrap:anywhere}
.bundle{font-size:11px;line-height:1.4;color:#637b98;overflow-wrap:anywhere}
.row{display:flex;align-items:baseline;justify-content:space-between;gap:12px;
padding:10px 0;border-top:1px solid #dbe4ef}
.label{font-size:11px;color:#607995;flex:none}
.value{font-size:12px;font-weight:650;text-align:right;
overflow-wrap:anywhere;min-width:0}
details{border-top:1px solid #dbe4ef;margin-top:2px;padding-top:10px}
summary{font-size:11px;font-weight:650;color:#164b83;cursor:pointer;
padding:3px 0 6px}
.technical{font-size:11px;line-height:1.5;color:#607995;
overflow-wrap:anywhere;padding:3px 0}
.technical b{color:#274565}
.footer{margin-top:10px;color:#6e83a0;font-size:9px;letter-spacing:.5px}
@media(prefers-color-scheme:dark){
body,.content{background:#12243c;color:#f0f5ff}
.bundle,.label,.technical,.footer{color:#a2b6cd}
.row,details{border-color:#344b67}
summary{color:#9ec9f7}
.technical b{color:#daeaff}
.appmark{background:#24619d}
}
"""

def _safe(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _app_name(bundle_id: str) -> str:
    """Produce a friendly fallback name without requiring App Store metadata."""
    last_segment = bundle_id.rsplit(".", 1)[-1]
    return last_segment.replace("-", " ").replace("_", " ").title() or "App Store"


def _verified_transaction(identity: dict[str, Any]) -> dict[str, Any]:
    """Only show transaction fields decoded and verified against the parent app."""
    token = identity.get("signedTransactionInfo")
    if not isinstance(token, str) or not token:
        return {}

    decoded = validate_transaction_token(
        token,
        str(identity.get("bundleId") or ""),
        identity.get("appAppleId"),
        str(identity.get("environment") or ""),
    )
    return decoded if isinstance(decoded, dict) else {}


def render_notification_widget(payload: dict[str, Any]) -> str:
    """Render a responsive, self-contained Telegram widget with no external assets."""
    data = payload.get("data")
    identity = data if isinstance(data, dict) else {}
    kind = str(payload.get("notificationType") or "UNKNOWN")
    title, description, symbol, theme = EVENTS.get(
        kind,
        (kind.replace("_", " ").title(), "New App Store activity", "✦", "other"),
    )
    bundle = str(identity.get("bundleId") or "Unknown app")
    app_name = _app_name(bundle)
    environment = str(identity.get("environment") or "Unknown")
    uuid = str(payload.get("notificationUUID") or "N/A")
    signed_date = payload.get("signedDate")
    timestamp = format_timestamp(signed_date) if isinstance(signed_date, int) else "N/A"
    transaction = _verified_transaction(identity)

    fields = []
    product_id = transaction.get("productId")
    if product_id:
        product = str(product_id).rsplit(".", 1)[-1].replace("_", " ").title()
        fields.append(("Product", product))
    ownership = transaction.get("inAppOwnershipType")
    if ownership:
        ownership_label = {
            "FAMILY_SHARED": "Family Sharing",
            "PURCHASED": "Purchased",
        }.get(str(ownership), str(ownership).replace("_", " ").title())
        fields.append(("Ownership", ownership_label))
    if transaction.get("storefront"):
        fields.append(("Storefront", transaction["storefront"]))
    fields.append(("Received", timestamp))

    rows = "".join(
        f'<div class="row"><span class="label">{_safe(label)}</span>'
        f'<span class="value">{_safe(value)}</span></div>'
        for label, value in fields
    )
    technical = [
        ("Event", kind),
        ("Environment", environment),
        ("Notification ID", uuid),
    ]
    if product_id:
        technical.append(("Product ID", product_id))
    technical_html = "".join(
        f'<div class="technical"><b>{_safe(label)}:</b> {_safe(value)}</div>'
        for label, value in technical
    )
    badge = "SANDBOX" if environment.casefold() == "sandbox" else "APP STORE"
    markup = "".join(
        [
            '<!doctype html><html><head><meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            "<style>",
            _CSS,
            "</style></head><body>",
            f'<section class="hero {theme}">',
            '<div class="top"><span class="brand">APPSTOREWEBHOOK</span>',
            f'<span class="pill">{badge}</span></div>',
            '<div class="heading">',
            f"<h1>{_safe(title)}</h1>",
            f'<span class="symbol">{_safe(symbol)}</span>',
            "</div>",
            f'<p class="description">{_safe(description)}</p>',
            '</section><section class="content"><div class="app">',
            f'<span class="appmark">{_safe(app_name[0].upper())}</span>',
            '<div>',
            f'<div class="appname">{_safe(app_name)}</div>',
            f'<div class="bundle">{_safe(bundle)}</div>',
            "</div></div>",
            rows,
            "<details><summary>Technical details</summary>",
            technical_html,
            '</details><div class="footer">APP STORE ACTIVITY</div>',
            "</section></body></html>",
        ]
    )
    raw = markup.encode("utf-8")
    if (
        len(raw) > MAX_HTML_BYTES
        or len(zlib.compress(raw, level=9)) > MAX_COMPRESSED_BYTES
    ):
        raise ValueError("Telegram widget exceeds HTML size limits")
    return markup
