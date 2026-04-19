"""
EcoSphere — Email Notification Service
Supports both SMTP (Gmail/any) and SendGrid
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM     = os.getenv("SMTP_FROM", "EcoSphere <noreply@ecosphere.in>")
SENDGRID_KEY  = os.getenv("SENDGRID_API_KEY", "")

# Production URL of the deployed frontend
APP_URL = os.getenv("APP_URL", "https://eco-sphere-rho-eosin.vercel.app")

# ── Base HTML Template ──────────────────────────────
def _html_wrapper(body: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#f5f9f6; margin:0; padding:0; }}
  .container {{ max-width:600px; margin:32px auto; background:#fff; border-radius:16px;
                border:1px solid #e0e8e2; overflow:hidden; }}
  .header {{ background:linear-gradient(135deg,#185f31,#1e7a3e); padding:28px 32px; }}
  .header h1 {{ margin:0; color:#fff; font-size:22px; font-weight:800; letter-spacing:-0.5px; }}
  .header p  {{ margin:6px 0 0; color:#a8d5b5; font-size:14px; }}
  .body  {{ padding:32px; }}
  .body p {{ color:#3a4a3d; font-size:15px; line-height:1.65; margin:0 0 16px; }}
  .cta   {{ display:inline-block; background:#1e7a3e; color:#fff; padding:12px 28px;
             border-radius:8px; font-weight:700; font-size:14px; text-decoration:none; margin:8px 0 20px; }}
  .cta-outline {{ display:inline-block; background:#fff; color:#1e7a3e; padding:10px 22px;
                  border-radius:8px; font-weight:700; font-size:14px; text-decoration:none;
                  margin:6px 6px 6px 0; border:2px solid #1e7a3e; }}
  .cta-danger {{ display:inline-block; background:#fff; color:#dc2626; padding:10px 22px;
                 border-radius:8px; font-weight:700; font-size:14px; text-decoration:none;
                 margin:6px 6px 6px 0; border:2px solid #dc2626; }}
  .cta-chat {{ display:inline-block; background:#fff; color:#0369a1; padding:10px 22px;
               border-radius:8px; font-weight:700; font-size:14px; text-decoration:none;
               margin:6px 6px 6px 0; border:2px solid #0369a1; }}
  .info-box {{ background:#f0faf2; border:1px solid #b8e8c5; border-radius:10px;
                padding:16px 20px; margin:16px 0; }}
  .info-box p {{ margin:4px 0; font-size:14px; color:#185f31; }}
  .action-row {{ display:flex; flex-wrap:wrap; gap:8px; margin:20px 0; }}
  .footer {{ background:#f0f5f1; padding:16px 32px; text-align:center;
              font-size:12px; color:#6b7a6e; border-top:1px solid #e0e8e2; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🌿 EcoSphere</h1>
    <p>India's B2B Circular Economy Platform</p>
  </div>
  <div class="body">{body}</div>
  <div class="footer">
    &copy; 2026 EcoSphere by IA (Innovators Arena) &nbsp;|&nbsp;
    <a href="{APP_URL}" style="color:#4caf71;">Visit Platform</a>
  </div>
</div>
</body></html>"""


# ── Core Send Function ──────────────────────────────
def send_email(to: str, subject: str, html_body: str, plain_body: str = "") -> bool:
    """Send email via SMTP. Returns True on success."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("Email not configured — SMTP_USER/SMTP_PASSWORD not set in .env")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SMTP_FROM
        msg["To"]      = to
        if plain_body:
            msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(_html_wrapper(html_body), "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to, msg.as_string())
        logger.info(f"✉️  Email sent to {to} — {subject}")
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to}: {e}")
        return False


# ── Template: Quote Request Received (Seller) ───────
def send_quote_received(
    seller_email: str,
    seller_company: str,
    buyer_company: str,
    listing_title: str,
    quantity: Optional[str],
    message: Optional[str],
    quote_id: int,
):
    subject = f"🌿 New Quote Request for \"{listing_title}\" — EcoSphere"
    # Accept / Reject links go back to the platform where the seller manages quotes
    body = f"""
<p>Hi <strong>{seller_company}</strong>,</p>
<p>Great news! You've received a new quote request on EcoSphere.</p>
<div class="info-box">
  <p>📦 <strong>Listing:</strong> {listing_title}</p>
  <p>🏭 <strong>From:</strong> {buyer_company}</p>
  <p>📊 <strong>Quantity Needed:</strong> {quantity or 'Not specified'}</p>
  <p>💬 <strong>Message:</strong> {message or 'No message provided'}</p>
  <p>🔖 <strong>Quote ID:</strong> #{quote_id}</p>
</div>
<p>Log in to EcoSphere and respond to this quote request:</p>
<div class="action-row">
  <a href="{APP_URL}/#chat" class="cta">💬 Accept & Chat</a>
  <a href="{APP_URL}" class="cta-outline">👀 View Request</a>
</div>
<p style="font-size:13px;color:#6b7a6e;">
  ℹ️ Click "Accept & Chat" to open the EcoSphere platform and start a conversation with the buyer.
</p>
"""
    plain = f"New quote request from {buyer_company} for {listing_title}. Quote #{quote_id}. Login to {APP_URL} to respond."
    send_email(seller_email, subject, body, plain)


# ── Template: Quote Request Sent (Buyer) ────────────
def send_quote_confirmation(
    buyer_email: str,
    buyer_company: str,
    seller_company: str,
    listing_title: str,
    quote_id: int,
):
    subject = f"✅ Quote Request Sent — {listing_title} | EcoSphere"
    body = f"""
<p>Hi <strong>{buyer_company}</strong>,</p>
<p>Your quote request has been successfully sent to <strong>{seller_company}</strong>.</p>
<div class="info-box">
  <p>📦 <strong>Listing:</strong> {listing_title}</p>
  <p>🏭 <strong>Seller:</strong> {seller_company}</p>
  <p>⏱️ <strong>Expected Response:</strong> Within 24–48 hours</p>
  <p>🔖 <strong>Quote ID:</strong> #{quote_id}</p>
</div>
<p>You'll receive an email notification once the seller responds to your request.</p>
<a href="{APP_URL}/#marketplace" class="cta">Track Your Requests →</a>
<p style="font-size:13px;color:#6b7a6e;">
  Once the seller accepts your quote, a chat channel will open between you and {seller_company}.
</p>
"""
    plain = f"Your quote for {listing_title} was sent to {seller_company}. Track at {APP_URL}"
    send_email(buyer_email, subject, body, plain)


# ── Template: Quote Status Update ───────────────────
def send_quote_status_update(
    recipient_email: str,
    recipient_company: str,
    listing_title: str,
    new_status: str,
    quote_id: int,
):
    status_map = {
        "accepted":  ("🎉 Quote Accepted", "#1e7a3e", "Your quote request has been ACCEPTED!",
                      f"You can now chat with the seller. Head to the Chat section on EcoSphere."),
        "rejected":  ("❌ Quote Declined", "#dc2626", "Unfortunately, your quote was declined.",
                      f"You can browse other listings and send new quote requests."),
        "completed": ("✅ Exchange Completed", "#185f31", "Your waste exchange has been marked as COMPLETED!",
                      f"Green Points have been awarded for this exchange. Check your Green Score dashboard."),
    }
    emoji, color, headline, detail = status_map.get(
        new_status,
        ("📋 Quote Updated", "#3a4a3d", "Your quote status has been updated.", "")
    )
    subject = f"{emoji} — {listing_title} | EcoSphere"
    chat_btn = f'<a href="{APP_URL}/#chat" class="cta-chat" style="margin-top:12px;">💬 Open Chat →</a>' if new_status == "accepted" else ""
    body = f"""
<p>Hi <strong>{recipient_company}</strong>,</p>
<p style="color:{color};font-weight:700;font-size:16px;">{headline}</p>
<div class="info-box">
  <p>📦 <strong>Listing:</strong> {listing_title}</p>
  <p>📋 <strong>Status:</strong> <span style="text-transform:capitalize;font-weight:700;">{new_status}</span></p>
  <p>🔖 <strong>Quote ID:</strong> #{quote_id}</p>
</div>
<p>{detail}</p>
<a href="{APP_URL}" class="cta">Open EcoSphere →</a>
{chat_btn}
"""
    plain = f"Quote #{quote_id} for {listing_title} is now {new_status}. Visit {APP_URL}"
    send_email(recipient_email, subject, body, plain)


# ── Template: New Listing Verified (Admin → Seller) ──
def send_listing_verified(
    seller_email: str,
    seller_company: str,
    listing_title: str,
    admin_note: Optional[str] = None,
):
    subject = f"✅ Your Listing \"{listing_title}\" is Verified! | EcoSphere"
    body = f"""
<p>Hi <strong>{seller_company}</strong>,</p>
<p>🎉 Your listing has been <strong>verified</strong> by the EcoSphere team and is now live on the marketplace!</p>
<div class="info-box">
  <p>📦 <strong>Listing:</strong> {listing_title}</p>
  <p>✅ <strong>Status:</strong> Verified &amp; Live</p>
  {f'<p>📝 <strong>Admin Note:</strong> {admin_note}</p>' if admin_note else ''}
</div>
<p>Verified listings receive priority placement and the Verified badge, leading to more buyer inquiries.</p>
<a href="{APP_URL}" class="cta">View Your Listing →</a>
"""
    plain = f"Your listing {listing_title} has been verified and is now live on EcoSphere! Visit {APP_URL}"
    send_email(seller_email, subject, body, plain)


# ── Template: Payment Confirmation ──────────────────
def send_payment_confirmation(
    buyer_email: str,
    buyer_company: str,
    listing_title: str,
    amount_inr: float,
    razorpay_payment_id: str,
):
    subject = f"🧾 Payment Confirmed — ₹{amount_inr:,.2f} | EcoSphere"
    body = f"""
<p>Hi <strong>{buyer_company}</strong>,</p>
<p>Your payment has been successfully processed on EcoSphere.</p>
<div class="info-box">
  <p>📦 <strong>Item:</strong> {listing_title}</p>
  <p>💰 <strong>Amount Paid:</strong> ₹{amount_inr:,.2f}</p>
  <p>🔖 <strong>Payment ID:</strong> {razorpay_payment_id}</p>
</div>
<p>Keep this email as your receipt. The seller will be notified and will arrange the material transfer.</p>
<a href="{APP_URL}" class="cta">View Transaction →</a>
"""
    plain = f"Payment of ₹{amount_inr:,.2f} confirmed for {listing_title}. Payment ID: {razorpay_payment_id}. Visit {APP_URL}"
    send_email(buyer_email, subject, body, plain)
