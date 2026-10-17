"""
mock_data.py - Realistic mock dataset for testing and sandbox demo mode.
Includes a realistic variety of marketing campaigns, large emails with heavy graphics/attachments,
protected purchases, hotel/flight bookings, bank statements, and personal emails.
"""

from datetime import datetime, timedelta
import random

def get_mock_emails(max_emails=None, order="newest"):
    now = datetime.now()
    
    mock_list = [
        # --- MARKETING (SOME VERY LARGE) ---
        {
            "id": "mock_1",
            "message_id": "<mock_1@fastfashion-style.com>",
            "subject": "🔥 SUMMER CLEARANCE: Up to 70% Off Everything + Free Delivery!",
            "sender": "offers@fastfashion-style.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=2)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 8_450_000, # 8.45 MB (Heavy marketing images)
            "headers": {
                "list-unsubscribe": "<https://fastfashion-style.com/unsub?id=99281>",
                "precedence": "bulk",
                "x-mailer": "Klaviyo Marketing Automation",
                "x-campaign": "summer_clearance_blast_01",
                "message-id": "<mock_1@fastfashion-style.com>"
            },
            "body_snippet": "Don't miss our biggest summer clearance sale ever! Huge discounts across all clothing, shoes and accessories with high-res lookbook images."
        },
        {
            "id": "mock_2",
            "message_id": "<mock_2@techinsights-weekly.io>",
            "subject": "Weekly Tech Digest: Top 10 AI Tools You Need This Month",
            "sender": "newsletter@techinsights-weekly.io",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=4)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 1_250_000, # 1.25 MB
            "headers": {
                "list-unsubscribe": "<mailto:unsub@techinsights-weekly.io>",
                "precedence": "list",
                "x-mailer": "Mailchimp Mailer v14",
                "message-id": "<mock_2@techinsights-weekly.io>"
            },
            "body_snippet": "Here is your weekly roundup of trending developer tools, AI updates, and engineering best practices. View online or unsubscribe anytime."
        },
        {
            "id": "mock_3",
            "message_id": "<mock_3@homedecor-direct.co.uk>",
            "subject": "20% Discount Code Inside - Weekend Special",
            "sender": "promotions@homedecor-direct.co.uk",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=6)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 12_800_000, # 12.8 MB (Huge image catalog)
            "headers": {
                "list-unsubscribe": "<https://homedecor-direct.co.uk/opt-out>",
                "precedence": "bulk",
                "x-mailer": "Sendgrid Campaigns",
                "message-id": "<mock_3@homedecor-direct.co.uk>"
            },
            "body_snippet": "Refresh your home interior with our new autumn furniture catalog! Use voucher code HOME20 at checkout for instant savings."
        },
        {
            "id": "mock_4",
            "message_id": "<mock_4@urban-kickz.com>",
            "subject": "Exclusive VIP Deals: Sneaker Drop Countdown",
            "sender": "deals@urban-kickz.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=8)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 4_600_000, # 4.6 MB
            "headers": {
                "list-unsubscribe": "<https://urban-kickz.com/unsubscribe>",
                "precedence": "bulk",
                "x-mailer": "Braze Marketing Cloud",
                "message-id": "<mock_4@urban-kickz.com>"
            },
            "body_snippet": "Get ready for the limited edition sneaker release. VIP access begins in 2 hours. Shop now before inventory sells out."
        },
        {
            "id": "mock_5",
            "message_id": "<mock_5@gadgetdepot.com>",
            "subject": "Your Daily Deal of the Day: Smart Home Accessories",
            "sender": "deals@gadgetdepot.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=9)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 750_000, # 750 KB
            "headers": {
                "list-unsubscribe": "<https://gadgetdepot.com/unsub>",
                "precedence": "bulk",
                "message-id": "<mock_5@gadgetdepot.com>"
            },
            "body_snippet": "Today only: Save 40% on smart bulbs, plugs, and motion sensors. Free shipping on orders over £30."
        },
        {
            "id": "mock_6",
            "message_id": "<mock_6@outdoors-gear.co.uk>",
            "subject": "Last Chance: Mega Clearance Sale ends midnight!",
            "sender": "marketing@outdoors-gear.co.uk",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=12)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 6_200_000, # 6.2 MB
            "headers": {
                "list-unsubscribe": "<https://outdoors-gear.co.uk/unsub>",
                "precedence": "bulk",
                "x-mailer": "Salesforce Marketing Cloud",
                "message-id": "<mock_6@outdoors-gear.co.uk>"
            },
            "body_snippet": "Final call for the outdoor summer clearance. Tents, hiking boots, and waterproof jackets up to 60% off."
        },
        {
            "id": "mock_7",
            "message_id": "<mock_7@quickgrocery.com>",
            "subject": "30% off your next grocery delivery with promo code FEAST30",
            "sender": "promotions@quickgrocery.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=14)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 850_000, # 850 KB
            "headers": {
                "list-unsubscribe": "<https://quickgrocery.com/email-preferences>",
                "precedence": "bulk",
                "message-id": "<mock_7@quickgrocery.com>"
            },
            "body_snippet": "Craving fresh snacks and ingredients? Order now and get 30% off with coupon code FEAST30. Valid until Sunday."
        },

        # --- PROTECTED: PURCHASES & RECEIPTS (MUST NEVER BE DELETED!) ---
        {
            "id": "mock_8",
            "message_id": "<mock_8@amazon.co.uk>",
            "subject": "Your Amazon.co.uk order #205-8492019-3829104 confirmation",
            "sender": "auto-confirm@amazon.co.uk",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=3)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 85_000,
            "headers": {
                "list-unsubscribe": "<https://amazon.co.uk/gp/gss/o/12345>", # Notice: Amazon has unsub, but must still be protected!
                "precedence": "bulk",
                "message-id": "<mock_8@amazon.co.uk>"
            },
            "body_snippet": "Thank you for your order! Your items will be dispatched soon. Order total: £42.99. View order details or print tax invoice."
        },
        {
            "id": "mock_9",
            "message_id": "<mock_9@uber.com>",
            "subject": "Your Uber trip receipt for £18.45 on Friday evening",
            "sender": "receipts@uber.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=5)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 42_000,
            "headers": {
                "message-id": "<mock_9@uber.com>"
            },
            "body_snippet": "Total: £18.45. Trip from Covent Garden to Victoria Station. Breakdown includes base fare, distance, and booking fee. Thank you for riding with Uber."
        },
        {
            "id": "mock_10",
            "message_id": "<mock_10@email.apple.com>",
            "subject": "Apple Services Tax Invoice #INV-99201488",
            "sender": "no_reply@email.apple.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=7)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 68_000,
            "headers": {
                "message-id": "<mock_10@email.apple.com>"
            },
            "body_snippet": "Apple invoice for iCloud+ 200GB storage plan (£2.99). Billed to your Mastercard ending in 4128."
        },
        {
            "id": "mock_11",
            "message_id": "<mock_11@deliveroo.co.uk>",
            "subject": "Your Deliveroo Order Receipt: Nando's (Order #DEL-48201)",
            "sender": "orders@deliveroo.co.uk",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=10)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 55_000,
            "headers": {
                "message-id": "<mock_11@deliveroo.co.uk>"
            },
            "body_snippet": "Payment received: £26.50. Estimated delivery time: 25-35 minutes. Track your courier in real-time."
        },

        # --- PROTECTED: BOOKINGS & TRAVEL (MUST NEVER BE DELETED!) ---
        {
            "id": "mock_12",
            "message_id": "<mock_12@britishairways.com>",
            "subject": "British Airways Flight Booking Confirmation: LHR to BCN (Ref: 7KQ9PZ)",
            "sender": "bookings@britishairways.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=11)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 140_000,
            "headers": {
                "message-id": "<mock_12@britishairways.com>"
            },
            "body_snippet": "Your flight BA0478 from London Heathrow (Terminal 5) to Barcelona El Prat is confirmed. PNR: 7KQ9PZ. Online check-in opens 24 hours prior."
        },
        {
            "id": "mock_13",
            "message_id": "<mock_13@booking.com>",
            "subject": "Booking.com Reservation Confirmed - Catalonia Ramblas Barcelona (PIN: 8821)",
            "sender": "customer.service@booking.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=11)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 115_000,
            "headers": {
                "list-unsubscribe": "<https://booking.com/unsub>",
                "message-id": "<mock_13@booking.com>"
            },
            "body_snippet": "Check-in: 15 Oct. Check-out: 18 Oct. Total price: €380.00. Free cancellation until 13 Oct. Address: Pelai 28, Barcelona."
        },
        {
            "id": "mock_14",
            "message_id": "<mock_14@eurostar.com>",
            "subject": "Eurostar e-Ticket and Travel Itinerary for London St Pancras to Paris Gare du Nord",
            "sender": "tickets@eurostar.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=18)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 310_000,
            "headers": {
                "message-id": "<mock_14@eurostar.com>"
            },
            "body_snippet": "Your electronic tickets and boarding barcodes are attached. Departure: 09:31 London St Pancras Int. Coach 5, Seat 42."
        },

        # --- PROTECTED: BANKING & SECURITY ---
        {
            "id": "mock_15",
            "message_id": "<mock_15@barclays.co.uk>",
            "subject": "Your Monthly Barclays Bank Statement is Ready (Account ending 9102)",
            "sender": "notifications@barclays.co.uk",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=15)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 450_000,
            "headers": {
                "message-id": "<mock_15@barclays.co.uk>"
            },
            "body_snippet": "Your monthly current account statement for September is now available to download securely in Online Banking or via the Barclays app."
        },
        {
            "id": "mock_16",
            "message_id": "<mock_16@account.google.com>",
            "subject": "One-Time Security Verification Code: 492019",
            "sender": "security-alert@account.google.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(hours=18)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 18_000,
            "headers": {
                "message-id": "<mock_16@account.google.com>"
            },
            "body_snippet": "Use 492019 to verify your Google Account. This code expires in 10 minutes. Do not share this OTP with anyone."
        },

        # --- GENERAL / PERSONAL (SOME LARGE ATTACHMENTS) ---
        {
            "id": "mock_17",
            "message_id": "<mock_17@gmail.com>",
            "subject": "Photos and 4K Video Clips from Lake District Weekend Hike",
            "sender": "david.walker@gmail.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=13)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 22_500_000, # 22.5 MB (Heavy personal attachment)
            "headers": {
                "message-id": "<mock_17@gmail.com>"
            },
            "body_snippet": "Hey Thomas! Here are the high-res photos and video clips from our Scafell Pike hike last Saturday. Hope you like them!"
        },
        {
            "id": "mock_18",
            "message_id": "<mock_18@company.com>",
            "subject": "Catch up for lunch next Tuesday?",
            "sender": "claire.jenkins@company.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=1)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 25_000,
            "headers": {
                "message-id": "<mock_18@company.com>"
            },
            "body_snippet": "Hi, let me know if you are free around 1pm next Tuesday for a quick sandwich and coffee near Oxford Circus!"
        },
        {
            "id": "mock_19",
            "message_id": "<mock_19@freelancedesign.org>",
            "subject": "Project Architecture Diagram & PDF Blueprint",
            "sender": "alex.m@freelancedesign.org",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=16)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 7_800_000, # 7.8 MB
            "headers": {
                "message-id": "<mock_19@freelancedesign.org>"
            },
            "body_snippet": "Attached is the latest revision of the wireframes, system architecture blueprint, and exportable vector assets."
        },
        {
            "id": "mock_20",
            "message_id": "<mock_20@eyewear-boutique.com>",
            "subject": "⚡ FLASH SALE: 40% Off Designer Eyewear & Sunglasses",
            "sender": "promotions@eyewear-boutique.com",
            "recipient": "user@example.com",
            "date": (now - timedelta(days=20)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "size_bytes": 3_900_000, # 3.9 MB
            "headers": {
                "list-unsubscribe": "<https://eyewear-boutique.com/unsubscribe>",
                "precedence": "bulk",
                "message-id": "<mock_20@eyewear-boutique.com>"
            },
            "body_snippet": "Upgrade your style with premium frames and lenses. Use coupon code SUNNY40. Unsubscribe if you no longer wish to receive promos."
        }
    ]

    for item in mock_list:
        if "message_id" not in item:
            item["message_id"] = f"<{item['id']}@mockmail.local>"
        if "message-id" not in item["headers"]:
            item["headers"]["message-id"] = item["message_id"]

    def parse_mock_date(m):
        try:
            return datetime.strptime(m["date"], "%a, %d %b %Y %H:%M:%S +0000")
        except Exception:
            return datetime.min

    if order in ("oldest", "start"):
        mock_list.sort(key=parse_mock_date)
    else:
        mock_list.sort(key=parse_mock_date, reverse=True)

    if max_emails and max_emails > 0 and len(mock_list) > max_emails:
        return mock_list[:max_emails]

    return mock_list
