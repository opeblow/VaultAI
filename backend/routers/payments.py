from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import hashlib
import hmac
import os

from backend.database import get_db
from backend.models.schemas import User, Payment, PaymentStatusEnum, ErrorResponse

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid signature"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


# =========================
# PRICES (NGN)
# =========================

PLAN_PRICES = {
    "creator_monthly": 5000,
    "studio_monthly": 10000
}


# =========================
# PYDANTIC SCHEMAS
# =========================

class Customer(BaseModel):
    email: str

class Metadata(BaseModel):
    plan: Optional[str] = None

class Data(BaseModel):
    customer: Customer
    amount: int
    reference: Optional[str] = None
    metadata: Optional[Metadata] = None

class WebhookPayload(BaseModel):
    event: str
    data: Data


# =========================
# SIGNATURE VERIFICATION
# =========================

def verify_paystack_signature(request_body: bytes, signature: str) -> bool:
    try:
        secret_key = os.getenv("PAYSTACK_SECRET_KEY", "")
        if not secret_key:
            return False
        
        computed_signature = hmac.new(
            secret_key.encode("utf-8"),
            request_body,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)
    except Exception:
        return False


# =========================
# PRODUCTION PAYSTACK WEBHOOK
# =========================

@router.post(
    "/webhook",
    summary="Paystack webhook endpoint",
    description="Handles Paystack webhook events with signature verification."
)
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_paystack_signature: Optional[str] = Header(None, alias="x-paystack-signature")
):
    try:
        body = await request.body()
        
        if not x_paystack_signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing x-paystack-signature header"
            )
        
        if not verify_paystack_signature(body, x_paystack_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        import json
        payload_dict = json.loads(body.decode("utf-8"))
        payload = WebhookPayload(**payload_dict)
        
        if payload.event != "charge.success":
            return Response(content="OK", status_code=200)
        
        email = payload.data.customer.email
        amount = payload.data.amount / 100
        plan_code = payload.data.metadata.plan if payload.data.metadata else None
        reference = payload.data.reference
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return Response(content="OK", status_code=200)
        
        existing = db.query(Payment).filter(Payment.reference == reference).first()
        if existing:
            return Response(content="OK", status_code=200)
        
        expected_amount = PLAN_PRICES.get(plan_code)
        if expected_amount is None or amount != expected_amount:
            return Response(content="OK", status_code=200)
        
        if plan_code == "studio_monthly":
            user.plan = "studio"
        elif plan_code == "creator_monthly":
            user.plan = "creator"
        
        payment = Payment(
            user_id=user.id,
            amount=amount,
            provider="paystack",
            status=PaymentStatusEnum.COMPLETED.value,
            reference=reference
        )
        
        db.add(payment)
        db.commit()
        
        return Response(content="OK", status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


# =========================
# SWAGGER TEST WEBHOOK
# =========================

@router.post("/webhook-test")
async def webhook_test(
    payload: WebhookPayload,
    db: Session = Depends(get_db)
):
    try:
        if payload.event != "charge.success":
            return {"message": "Ignored event"}
        
        email = payload.data.customer.email
        amount = payload.data.amount / 100
        plan_code = payload.data.metadata.plan if payload.data.metadata else None
        reference = payload.data.reference
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        existing = db.query(Payment).filter(Payment.reference == reference).first()
        if existing:
            return {"message": "Already processed"}
        
        expected_amount = PLAN_PRICES.get(plan_code)
        if expected_amount is None:
            raise HTTPException(status_code=400, detail="Invalid plan")
        
        if amount != expected_amount:
            raise HTTPException(status_code=400, detail="Amount mismatch")
        
        if plan_code == "studio_monthly":
            user.plan = "studio"
        else:
            user.plan = "creator"
        
        payment = Payment(
            user_id=user.id,
            amount=amount,
            provider="swagger-test",
            status=PaymentStatusEnum.COMPLETED.value,
            reference=reference
        )
        
        db.add(payment)
        db.commit()
        
        return {
            "message": "Swagger test successful",
            "email": email,
            "plan": user.plan,
            "amount": amount
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test webhook failed: {str(e)}"
        )

    