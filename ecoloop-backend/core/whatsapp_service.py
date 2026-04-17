"""
EcoSphere — WhatsApp Notification Service
Uses Twilio WhatsApp Business API
Set up: https://www.twilio.com/whatsapp
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TWILIO_SID      = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WA_FROM  = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


def _get_client():
    """Lazy-load Twilio client only when needed."""
    if not TWILIO_SID or not TWILIO_TOKEN:
        return None
    try:
        from twilio.rest import Client
        return Client(TWILIO_SID, TWILIO_TOKEN)
    except ImportError:
        logger.warning("Twilio not installed. Run: pip install twilio")
        return None
    except Exception as e:
        logger.error(f"Twilio init error: {e}")
        return None


def _format_wa_number(phone: str) -> str:
    """Format phone number to WhatsApp format."""
    # Remove spaces, dashes, etc.
    digits = "".join(filter(str.isdigit, phone))
    # Add India country code if not present
    if not digits.startswith("91") and len(digits) == 10:
        digits = "91" + digits
    return f"whatsapp:+{digits}"


def send_whatsapp(to_phone: str, message: str) -> bool:
    """Send a WhatsApp message. Returns True on success."""
    client = _get_client()
    if not client:
        logger.warning(f"WhatsApp not configured — skipping message to {to_phone}")
        return False
    try:
        wa_to = _format_wa_number(to_phone)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_WA_FROM,
            to=wa_to
        )
        logger.info(f"📱 WhatsApp sent to {wa_to} — SID: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp send failed to {to_phone}: {e}")
        return False


# ── WhatsApp Message Templates ──────────────────────

def wa_new_quote_alert(
    seller_phone: str,
    seller_company: str,
    buyer_company: str,
    listing_title: str,
    quantity: Optional[str],
    quote_id: int,
):
    """Alert seller on WhatsApp when they receive a quote request."""
    msg = (
        f"🌿 *EcoSphere Alert*\n\n"
        f"📦 New quote request received!\n\n"
        f"*Listing:* {listing_title}\n"
        f"*Buyer:* {buyer_company}\n"
        f"*Quantity:* {quantity or 'Not specified'}\n\n"
        f"Quote ID: #{quote_id}\n\n"
        f"Log in to EcoSphere to respond ➜ http://localhost:8000"
    )
    return send_whatsapp(seller_phone, msg)


def wa_quote_accepted(
    buyer_phone: str,
    buyer_company: str,
    seller_company: str,
    listing_title: str,
    quote_id: int,
):
    """Notify buyer on WhatsApp when their quote is accepted."""
    msg = (
        f"🌿 *EcoSphere Alert*\n\n"
        f"🎉 Your quote request was *ACCEPTED*!\n\n"
        f"*Listing:* {listing_title}\n"
        f"*Seller:* {seller_company}\n\n"
        f"The seller will contact you shortly to arrange the exchange.\n\n"
        f"Quote ID: #{quote_id}\n"
        f"EcoSphere ➜ http://localhost:8000"
    )
    return send_whatsapp(buyer_phone, msg)


def wa_quote_rejected(
    buyer_phone: str,
    listing_title: str,
    seller_company: str,
    quote_id: int,
):
    """Notify buyer on WhatsApp when their quote is rejected."""
    msg = (
        f"🌿 *EcoSphere Alert*\n\n"
        f"❌ Your quote request was declined.\n\n"
        f"*Listing:* {listing_title}\n"
        f"*Seller:* {seller_company}\n\n"
        f"Don't worry! Browse more listings on EcoSphere.\n"
        f"➜ http://localhost:8000\n\n"
        f"Quote ID: #{quote_id}"
    )
    return send_whatsapp(buyer_phone, msg)


def wa_exchange_completed(
    phone: str,
    company: str,
    listing_title: str,
    quote_id: int,
):
    """Notify both parties on exchange completion."""
    msg = (
        f"🌿 *EcoSphere Alert*\n\n"
        f"✅ Exchange *COMPLETED*!\n\n"
        f"*Material:* {listing_title}\n"
        f"*Company:* {company}\n\n"
        f"🌱 Great job! Green Points have been added to your account.\n"
        f"You can now rate this exchange on EcoSphere.\n\n"
        f"Quote ID: #{quote_id}\n"
        f"EcoSphere ➜ http://localhost:8000"
    )
    return send_whatsapp(phone, msg)


def wa_listing_verified(
    seller_phone: str,
    seller_company: str,
    listing_title: str,
):
    """Notify seller when their listing is verified by admin."""
    msg = (
        f"🌿 *EcoSphere Alert*\n\n"
        f"✅ Your listing is *VERIFIED* and live!\n\n"
        f"*Listing:* {listing_title}\n"
        f"*Company:* {seller_company}\n\n"
        f"Your listing now has the Verified badge and gets priority placement.\n\n"
        f"EcoSphere ➜ http://localhost:8000"
    )
    return send_whatsapp(seller_phone, msg)


def wa_payment_confirmed(
    buyer_phone: str,
    listing_title: str,
    amount_inr: float,
    payment_id: str,
):
    """Notify buyer when payment is confirmed."""
    msg = (
        f"🌿 *EcoSphere Payment*\n\n"
        f"💰 Payment *CONFIRMED*!\n\n"
        f"*Material:* {listing_title}\n"
        f"*Amount:* ₹{amount_inr:,.2f}\n"
        f"*Payment ID:* {payment_id}\n\n"
        f"The seller will arrange material pickup/delivery.\n"
        f"EcoSphere ➜ http://localhost:8000"
    )
    return send_whatsapp(buyer_phone, msg)
