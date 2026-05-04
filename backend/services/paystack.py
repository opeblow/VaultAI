from paystackapi.paystack import Paystack
from config import settings
from models.user import User
from models.payment import Payment
from sqlalchemy.orm import Session

paystack = Paystack(secret_key=settings.PAYSTACK_SECRET_KEY)


def initialize_transaction(email: str, amount: int, callback_url: str | None = None) -> dict:
    payload = {
        "email": email,
        "amount": amount,
    }
    if callback_url:
        payload["callback_url"] = callback_url
    return paystack.transaction.initialize(**payload)


def verify_transaction(reference: str) -> dict:
    return paystack.transaction.verify(reference)


def handle_webhook(event: str, data: dict, db: Session) -> dict:
    from fastapi import HTTPException, status

    if event == "charge.success":
        paystack_ref = data.get("reference")
        if not paystack_ref:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing reference")

        user_email = data.get("customer", {}).get("email")
        if not user_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing customer email")

        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.plan = "premium"
        db.add(user)

        payment = Payment(
            user_id=user.id,
            paystack_ref=paystack_ref,
            amount=data.get("amount", 0),
            currency=data.get("currency", "NGN"),
            status="success",
        )
        db.add(payment)
        db.commit()

        return {"status": "success", "message": "Payment processed and user upgraded to premium"}

    return {"status": "ignored", "message": f"Event {event} not handled"}
