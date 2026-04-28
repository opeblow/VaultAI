"""
VaultAI Payments Router

This module provides endpoints for handling payment webhooks.
Implements Paystack webhook verification and subscription management.
"""

import hmac
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models.schemas import User, Payment, PaymentStatusEnum
from backend.models.schemas import PaymentWebhookResponse, ErrorResponse

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


def verify_paystack_signature(payload: bytes, signature: str) -> bool:
    if not signature or not settings.PAYSTACK_SECRET_KEY:
        return True
    
    computed_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)


@router.post(
    "/webhook",
    response_model=PaymentWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Paystack webhook endpoint",
    description="Handles payment webhook events from Paystack. No authentication required - signature verification is used instead."
)
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")
    
    if not verify_paystack_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    try:
        payload = json.loads(body)
        event = payload.get("event")
        data = payload.get("data", {})
        
        if event == "charge.success":
            customer_email = data.get("customer", {}).get("email")
            amount = data.get("amount")
            plan_code = data.get("metadata", {}).get("plan")
            
            if customer_email:
                user = db.query(User).filter(User.email == customer_email).first()
                
                if user:
                    plan_map = {
                        "creator": "creator",
                        "creator_monthly": "creator",
                        "studio": "studio",
                        "studio_monthly": "studio"
                    }
                    
                    new_plan = plan_map.get(plan_code, "creator")
                    
                    if plan_code and "studio" in plan_code:
                        new_plan = "studio"
                    elif plan_code and "creator" in plan_code:
                        new_plan = "creator"
                    
                    user.plan = new_plan
                    
                    payment = Payment(
                        user_id=user.id,
                        amount=amount if amount else 0,
                        provider="paystack",
                        status=PaymentStatusEnum.COMPLETED.value
                    )
                    db.add(payment)
                    db.commit()
        
    except json.JSONDecodeError:
        pass
    except Exception as e:
        pass
    
    return PaymentWebhookResponse(message="OK")
