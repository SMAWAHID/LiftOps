
import os
import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

print(f"Using key: {stripe.api_key[:8]}...")

try:
    intent = stripe.PaymentIntent.create(
        amount=9900,
        currency="usd",
        automatic_payment_methods={"enabled": True},
        metadata={"email": "test@example.com", "target_tier": "commander"},
    )
    print("Success! Client Secret:", intent.client_secret)
except Exception as e:
    print("Error:", str(e))
