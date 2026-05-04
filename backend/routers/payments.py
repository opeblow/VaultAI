from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
import hmac
import hashlib

from backend.config import settings
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.schemas.payment import PaymentInit, PaymentWebhook, PaymentResponse
from backend.services.paystack import initialize_transaction, verify_transaction, handle_webhook

router = APIRouter(tags=["Payments"])


@router.post(
    "/initialize",
    response_model=PaymentResponse,
    dependencies=[Depends(get_current_user)],
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "amount": 500000,
                        "email": "user@example.com",
                        "callback_url": "https://example.com/payment/callback",
                    }
                }
            }
        }
    },
)
def initialize_payment(payment: PaymentInit, db: Session = Depends(get_db)):
    result = initialize_transaction(payment.email, payment.amount, payment.callback_url)
    return PaymentResponse(status="success", message="Payment initialized", data=result)


@router.post(
    "/webhook",
    response_model=PaymentResponse,
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "event": "charge.success",
                        "data": {
                            "reference": "PY123456789",
                            "status": "success",
                            "amount": 500000,
                            "customer": {"email": "user@example.com"},
                        }
                    }
                }
            }
        }
    },
)
async def paystack_webhook(request: Request, webhook: PaymentWebhook):
    signature = request.headers.get("x-paystack-signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    payload = await request.body()
    expected_signature = hmac.new(
        settings.PAYSTACK_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    result = handle_webhook(webhook.event, webhook.data)
    return PaymentResponse(status="success", message="Webhook processed", data=result)


@router.get(
    "/verify/{reference}",
    response_model=PaymentResponse,
    openapi_extra={
        "responses": {
            200: {
                "content": {
                    "application/json": {
                        "example": {
                            "status": "success",
                            "message": "Payment verified",
                            "data": {
                                "reference": "PY123456789",
                                "status": "success",
                                "amount": 500000,
                            }
                        }
                    }
                }
            }
        }
    },
)
def verify_payment(reference: str, db: Session = Depends(get_db)):
    result = verify_transaction(reference)
    return PaymentResponse(status="success", message="Payment verified", data=result)
