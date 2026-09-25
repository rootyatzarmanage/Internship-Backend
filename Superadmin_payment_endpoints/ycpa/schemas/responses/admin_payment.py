from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel

class PaymentStatus(str,Enum):
    SUCCESS = "success"
    FAILED = "failed"
    INPROCESS = "inprocess"
    CREATED = "created"

class PaymentMethod(str,Enum):
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMI = "emi"
    PAYLATER = "paylater"
    BANK_TRANSFER = "bank_transfer"
    EMANDATE = "emandate"
    CARDLESS_EMI = "cardless_emi"
    ACH = "ach"
    APPLE_PAY = "apple_pay"

class AdminPaymentItemResponse(BaseModel):
    sales_no: str
    plan: str
    user_id: UUID
    user_name: str
    user_email: str
    amount: int
    currency: str
    payment_method: str | None
    payment_status: str
    date: datetime

class AdminPaymentResponse(BaseModel):
    items: list[AdminPaymentItemResponse]
    total: int