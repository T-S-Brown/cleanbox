"""
test_classifier.py - Unit tests verifying email categorization and safety rules.
"""

from classifier import classify_email

def test_order_with_unsubscribe_header_is_protected():
    """Crucial test: Receipts/orders with List-Unsubscribe must NEVER be deleted."""
    headers = {
        "List-Unsubscribe": "<https://example.com/unsub>",
        "Precedence": "bulk"
    }
    result = classify_email(
        subject="Your Amazon.co.uk order #205-1234567-8901234 confirmation",
        sender="auto-confirm@amazon.co.uk",
        headers=headers,
        size_bytes=45000
    )
    assert result["is_protected"] is True, "Order must be protected!"
    assert result["is_marketing"] is False, "Order must not be classified as marketing!"
    assert result["category"] == "PROTECTED"
    print("✓ Order with unsubscribe header correctly protected")

def test_flight_booking_protected():
    result = classify_email(
        subject="British Airways Flight Booking Confirmation: BA1492 LHR to JFK",
        sender="bookings@britishairways.com",
        headers={},
        size_bytes=120000
    )
    assert result["is_protected"] is True
    assert result["category"] == "PROTECTED"
    print("✓ Flight booking correctly protected")

def test_hotel_reservation_protected():
    result = classify_email(
        subject="Booking.com Reservation Confirmed - The Grand Hotel Paris",
        sender="customer.service@booking.com",
        headers={},
        size_bytes=98000
    )
    assert result["is_protected"] is True
    assert result["category"] == "PROTECTED"
    print("✓ Hotel reservation correctly protected")

def test_bank_statement_protected():
    result = classify_email(
        subject="Your Monthly Barclays Account Statement is Ready",
        sender="notifications@barclays.co.uk",
        headers={},
        size_bytes=240000
    )
    assert result["is_protected"] is True
    print("✓ Bank statement correctly protected")

def test_marketing_newsletter():
    headers = {
        "List-Unsubscribe": "<mailto:unsub@store.com>",
        "Precedence": "bulk",
        "X-Mailer": "Mailchimp Mailer v12"
    }
    result = classify_email(
        subject="50% OFF Flash Sale - This Weekend Only!",
        sender="newsletter@fashionbrand.com",
        headers=headers,
        size_bytes=3500000 # 3.5 MB
    )
    assert result["is_protected"] is False
    assert result["is_marketing"] is True
    assert result["is_large"] is True
    assert result["size_category"] == "large"
    assert result["category"] == "MARKETING"
    print("✓ Marketing newsletter correctly detected with large size flag")

def test_large_general_email():
    """Personal email with large attachment: should not be marked marketing."""
    result = classify_email(
        subject="Photos from family holiday in Spain",
        sender="sarah.smith@example.com",
        headers={},
        size_bytes=15 * 1024 * 1024 # 15 MB
    )
    assert result["is_protected"] is False
    assert result["is_marketing"] is False
    assert result["is_large"] is True
    assert result["size_category"] == "huge"
    assert result["category"] == "GENERAL"
    print("✓ Large personal email flagged by size without being marked marketing")

if __name__ == "__main__":
    test_order_with_unsubscribe_header_is_protected()
    test_flight_booking_protected()
    test_hotel_reservation_protected()
    test_bank_statement_protected()
    test_marketing_newsletter()
    test_large_general_email()
    print("\nALL CLASSIFIER TESTS PASSED SUCCESSFULLY! 🎉")
