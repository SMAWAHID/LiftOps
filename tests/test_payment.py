from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

@patch("stripe.PaymentIntent.create")
def test_create_payment_intent(mock_stripe_create):
    mock_stripe_create.return_value = MagicMock(client_secret="secret_123")
    
    response = client.post("/api/create-payment-intent", json={"email": "test@example.com"})
    assert response.status_code == 200
    assert response.json() == {"clientSecret": "secret_123"}
    mock_stripe_create.assert_called_once()

@patch("stripe.PaymentIntent.retrieve")
@patch("main.user_repo")
def test_verify_payment_success(mock_user_repo, mock_stripe_retrieve):
    # Mock Stripe success
    mock_intent = MagicMock()
    mock_intent.status = "succeeded"
    mock_intent.metadata = {"email": "test@example.com"}
    mock_stripe_retrieve.return_value = mock_intent
    
    # Mock User Repo
    mock_user_repo.upgrade_tier.return_value = {"email": "test@example.com", "tier": "commander"}
    
    response = client.post("/api/verify-payment", json={"paymentIntentId": "pi_123"})
    
    assert response.status_code == 200
    assert response.json()["user"]["tier"] == "commander"
    mock_user_repo.upgrade_tier.assert_called_with("test@example.com", "commander")

@patch("stripe.PaymentIntent.retrieve")
def test_verify_payment_pending(mock_stripe_retrieve):
    mock_intent = MagicMock()
    mock_intent.status = "requires_payment_method"
    mock_stripe_retrieve.return_value = mock_intent
    
    response = client.post("/api/verify-payment", json={"paymentIntentId": "pi_123"})
    
    assert response.json()["status"] == "pending"
