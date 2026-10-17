"""
classifier.py - Email classification engine for Cleanbox.

Categorizes emails into:
1. PROTECTED (Purchases, bookings, travel itineraries, receipts, bank statements, security codes)
   - ALWAYS protected with top priority to prevent accidental deletion!
2. MARKETING (Newsletters, promotional offers, sales, bulk campaigns)
   - Identified via RFC List-Unsubscribe, Precedence: bulk, marketing mailers, and promotional indicators.
3. LARGE EMAILS
   - Flagged by size (>= 1MB, >= 5MB, >= 10MB) to maximize space recovery.
"""

import re
from typing import Dict, List, Any, Optional

# Regex patterns for protected transactional & important emails
PROTECTED_PATTERNS = [
    # Purchases & Receipts
    (r"\b(order\s+(?:confirmation|placed|summary|update|#|number))\b", "Order confirmation"),
    (r"\b(receipt|e-receipt|tax\s+invoice|vat\s+invoice|sales\s+receipt)\b", "Purchase receipt or invoice"),
    (r"\b(invoice\s+(?:#|number|attached|due|paid))\b", "Invoice document"),
    (r"\b(your\s+order\s+with|your\s+order\s+from|thank\s+you\s+for\s+your\s+order)\b", "Order placement"),
    (r"\b(payment\s+(?:received|confirmed|confirmation|processed|successful|receipt))\b", "Payment confirmation"),
    (r"\b(billing\s+statement|account\s+statement|bank\s+statement)\b", "Financial / Bank statement"),
    (r"\b(apple\s+services\s+receipt|google\s+play\s+order|app\s+store\s+receipt)\b", "Digital store purchase receipt"),
    (r"\b(subscription\s+(?:confirmed|started|renewed|payment))\b", "Active subscription receipt"),
    (r"\b(refund\s+(?:confirmation|issued|processed|notice))\b", "Refund notification"),

    # Bookings & Travel
    (r"\b(booking\s+(?:confirmation|reference|confirmed|details|ref))\b", "Booking confirmation"),
    (r"\b(reservation\s+(?:confirmation|confirmed|details|code))\b", "Reservation details"),
    (r"\b(flight\s+(?:confirmation|booking|details|itinerary|ticket|e-ticket|eticket))\b", "Flight itinerary / confirmation"),
    (r"\b(boarding\s+pass|check-in\s+confirmation|passenger\s+receipt)\b", "Boarding pass / Travel document"),
    (r"\b(hotel\s+(?:booking|reservation|stay))\b", "Hotel reservation"),
    (r"\b(car\s+rental\s+(?:booking|reservation|confirmation))\b", "Car rental confirmation"),
    (r"\b(airbnb\s+(?:reservation|booking|itinerary))\b", "Airbnb reservation"),
    (r"\b(trainline|eurostar|amtrak|national\s+rail|uber\s+trip\s+receipt)\b", "Transport ticket / receipt"),
    (r"\b(pnr\s*[:#]|e-ticket\s*receipt)\b", "Travel PNR / Ticket receipt"),
    (r"\b(ticket\s+confirmation|event\s+ticket|concert\s+ticket)\b", "Event ticket confirmation"),

    # Delivery & Shipping
    (r"\b(your\s+package\s+(?:has\s+shipped|is\s+on\s+the\s+way|delivered|has\s+arrived))\b", "Package shipping / delivery"),
    (r"\b(shipping\s+confirmation|dispatch\s+confirmation|delivery\s+confirmation)\b", "Dispatch confirmation"),
    (r"\b(tracking\s+(?:number|details|link|id))\b", "Package tracking details"),

    # Security & Accounts
    (r"\b(verification\s+code|security\s+code|one-time\s+pass(?:code|word)|otp)\b", "Verification / Security code"),
    (r"\b(password\s+reset|reset\s+your\s+password|account\s+recovery)\b", "Account security notification"),
    (r"\b(two-factor|2-step|2fa\s+code|login\s+alert|new\s+sign-in)\b", "Security login alert"),

    # Legal, Government & Healthcare
    (r"\b(tax\s+(?:return|form|document)|w-2|1099|p60|p45|hmrc|irs)\b", "Tax / Government document"),
    (r"\b(appointment\s+(?:reminder|confirmation|scheduled))\b", "Appointment confirmation"),
    (r"\b(prescription|lab\s+results|medical\s+record|clinic\s+appointment)\b", "Healthcare / Medical document"),
    (r"\b(contract\s+(?:signed|agreement)|terms\s+of\s+service\s+update)\b", "Legal contract / document"),
]

# High-priority protected sender patterns (e-commerce orders, banks, travel)
PROTECTED_SENDER_PATTERNS = [
    (r"auto-confirm@amazon\.", "Amazon Order Confirmation"),
    (r"shipment-tracking@amazon\.", "Amazon Delivery Notification"),
    (r"order.*@|receipts?@|invoicing?@|billing@|payments?@", "Transactional billing address"),
    (r"no-reply@uber\.com|receipts@uber\.com", "Uber Ride / Eats Receipt"),
    (r"no-reply@booking\.com|customer\.service@booking\.com", "Booking.com Reservation"),
    (r"automated@airbnb\.com", "Airbnb Reservation"),
    (r"service@paypal\.", "PayPal Transaction Confirmation"),
    (r"service@stripe\.", "Stripe Payment Receipt"),
    (r"orders@deliveroo\.", "Deliveroo Order Receipt"),
]

# Marketing subject keywords
MARKETING_SUBJECT_PATTERNS = [
    (r"\b(\d{1,2}%\s*off)\b", "Discount percentage offer"),
    (r"\b(sale\s+ends|mega\s+sale|flash\s+sale|clearance\s+sale|summer\s+sale|winter\s+sale|spring\s+sale)\b", "Promotional sale"),
    (r"\b(exclusive\s+(?:deal|offer|discount|savings))\b", "Promotional discount"),
    (r"\b(promo\s+code|discount\s+code|coupon\s+code|voucher\s+code)\b", "Promotional coupon code"),
    (r"\b(free\s+shipping\s+on\s+all|free\s+delivery\s+this\s+weekend)\b", "Free shipping promo"),
    (r"\b(don't\s+miss\s+out|last\s+chance\s+to\s+save|final\s+hours|ends\s+tonight)\b", "Urgency marketing copy"),
    (r"\b(weekly\s+(?:digest|roundup|newsletter)|monthly\s+newsletter)\b", "Recurring newsletter"),
    (r"\b(new\s+arrivals|shop\s+now|curated\s+picks|trending\s+this\s+week)\b", "Retail showcase"),
    (r"\b(black\s+friday|cyber\s+monday|prime\s+day|boxing\s+day\s+sale)\b", "Seasonal shopping event"),
    (r"\b(special\s+invitation|rewards\s+update|earn\s+double\s+points)\b", "Loyalty marketing"),
]

# Marketing sender address patterns
MARKETING_SENDER_PATTERNS = [
    (r"^newsletter@", "Newsletter inbox"),
    (r"^marketing@", "Marketing address"),
    (r"^promotions?@", "Promotions address"),
    (r"^deals?@", "Deals address"),
    (r"^offers?@", "Offers address"),
    (r"^campaigns?@", "Campaign address"),
    (r"^news@", "News broadcast address"),
    (r"^updates?@", "Updates broadcast address"),
]

# Marketing mailer header signatures
MARKETING_MAILER_HEADERS = [
    "mailchimp", "sendgrid", "klaviyo", "braze", "marketo", "hubspot",
    "salesforce", "campaign monitor", "constant contact", "sailthru",
    "activecampaign", "convertkit", "mailerlite", "sendinblue", "brevo"
]

LARGE_SIZE_BYTES_1MB = 1 * 1024 * 1024
LARGE_SIZE_BYTES_5MB = 5 * 1024 * 1024
LARGE_SIZE_BYTES_10MB = 10 * 1024 * 1024


def format_bytes(size_bytes: int) -> str:
    """Format size in bytes to human-readable string (KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def classify_email(
    subject: str,
    sender: str,
    headers: Dict[str, str],
    size_bytes: int = 0,
    body_snippet: str = ""
) -> Dict[str, Any]:
    """
    Classify an email into PROTECTED, MARKETING, or GENERAL.
    Also flags whether it is a LARGE email.

    CRITICAL RULE:
    Protected rules have absolute priority over marketing detection!
    Even if a receipt contains 'List-Unsubscribe', it MUST be protected.
    """
    subject_clean = (subject or "").strip()
    sender_clean = (sender or "").strip().lower()
    subject_lower = subject_clean.lower()
    snippet_lower = (body_snippet or "").lower()

    protection_reasons: List[str] = []
    marketing_reasons: List[str] = []

    # 1. Check for Protected Sender patterns
    for pat, desc in PROTECTED_SENDER_PATTERNS:
        if re.search(pat, sender_clean, re.IGNORECASE):
            protection_reasons.append(f"Sender match: {desc}")
            break

    # 2. Check for Protected Subject patterns
    for pat, desc in PROTECTED_PATTERNS:
        if re.search(pat, subject_lower):
            protection_reasons.append(f"Subject match: {desc}")
            break

    # 3. Check for Protected Snippet patterns (if subject wasn't conclusive)
    if not protection_reasons and snippet_lower:
        for pat, desc in PROTECTED_PATTERNS:
            if re.search(pat, snippet_lower[:500]):  # check top 500 chars
                protection_reasons.append(f"Content match: {desc}")
                break

    # 4. Check for Marketing indicators (headers, subject, sender)
    # Check List-Unsubscribe header (RFC 2369)
    list_unsub = headers.get("list-unsubscribe") or headers.get("List-Unsubscribe") or ""
    if list_unsub:
        marketing_reasons.append("Contains 'List-Unsubscribe' header (Standard bulk/marketing email)")

    # Check Precedence header
    precedence = (headers.get("precedence") or headers.get("Precedence") or "").lower()
    if precedence in ("bulk", "list", "junk"):
        marketing_reasons.append(f"Bulk precedence header: '{precedence}'")

    # Check X-Mailer or Mailer signatures
    x_mailer = (headers.get("x-mailer") or headers.get("X-Mailer") or "").lower()
    for signature in MARKETING_MAILER_HEADERS:
        if signature in x_mailer:
            marketing_reasons.append(f"Sent via marketing platform: {signature.capitalize()}")
            break

    # Check Campaign headers
    if headers.get("x-campaign") or headers.get("x-campaign-id") or headers.get("x-mailgun-campaign-id"):
        marketing_reasons.append("Includes marketing campaign tracking header")

    # Check Marketing Subject patterns
    for pat, desc in MARKETING_SUBJECT_PATTERNS:
        if re.search(pat, subject_lower):
            marketing_reasons.append(f"Subject match: {desc}")
            break

    # Check Marketing Sender patterns
    for pat, desc in MARKETING_SENDER_PATTERNS:
        if re.search(pat, sender_clean):
            marketing_reasons.append(f"Marketing sender pattern: {desc}")
            break

    # If snippet has clear unsubscribe footer and no protection
    if "unsubscribe" in snippet_lower and "opt out" in snippet_lower:
        if not any("Unsubscribe" in r for r in marketing_reasons):
            marketing_reasons.append("Email body contains unsubscribe / opt-out instructions")

    # Determine status:
    # RULE: If ANY protection reason matched, the email is PROTECTED!
    is_protected = len(protection_reasons) > 0
    is_marketing = not is_protected and len(marketing_reasons) > 0

    # Size classification
    is_large = size_bytes >= LARGE_SIZE_BYTES_1MB
    size_category = "normal"
    if size_bytes >= LARGE_SIZE_BYTES_10MB:
        size_category = "huge"  # > 10MB
    elif size_bytes >= LARGE_SIZE_BYTES_5MB:
        size_category = "very_large"  # 5 - 10MB
    elif size_bytes >= LARGE_SIZE_BYTES_1MB:
        size_category = "large"  # 1 - 5MB

    # Calculate marketing confidence score (0 - 100)
    marketing_score = 0
    if is_marketing:
        score = 0
        if list_unsub:
            score += 50
        if precedence in ("bulk", "list"):
            score += 20
        if any("Sent via marketing" in r for r in marketing_reasons):
            score += 15
        if any("Subject match" in r for r in marketing_reasons):
            score += 15
        if any("Marketing sender" in r for r in marketing_reasons):
            score += 10
        marketing_score = min(100, max(40, score))

    return {
        "is_protected": is_protected,
        "is_marketing": is_marketing,
        "is_large": is_large,
        "size_category": size_category,
        "size_bytes": size_bytes,
        "size_formatted": format_bytes(size_bytes),
        "marketing_score": marketing_score,
        "protection_reasons": protection_reasons,
        "marketing_reasons": marketing_reasons,
        "category": "PROTECTED" if is_protected else ("MARKETING" if is_marketing else "GENERAL"),
    }
