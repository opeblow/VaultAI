import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class PaymentInit(BaseModel):
    amount: int
    email: str
    callback_url: Optional[str] = None


class PaymentWebhook(BaseModel):
    event: str
    data: Dict


class PaymentResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict] = None
