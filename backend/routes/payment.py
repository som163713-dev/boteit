from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.models import Payment, Customer
from backend.auth import get_customer
from datetime import datetime, timedelta
import requests
import os

router = APIRouter(prefix="/payment", tags=["Payment"])

ZARINPAL_MERCHANT = os.getenv("ZARINPAL_MERCHANT", "")
ZARINPAL_REQUEST  = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY   = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_START    = "https://www.zarinpal.com/pg/StartPay/"

PLANS = {
    "basic":      {"price": 290000,  "days": 30, "name": "پایه"},
    "pro":        {"price": 690000,  "days": 30, "name": "حرفه‌ای"},
    "enterprise": {"price": 1490000, "days": 30, "name": "سازمانی"}
}

class PaymentRequest(BaseModel):
    api_key: str
    plan:    str

@router.get("/plans")
async def get_plans():
    return PLANS

@router.post("/request")
async def payment_request(
    req: PaymentRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    customer = get_customer(req.api_key, db)
    plan     = PLANS.get(req.plan)

    if not plan:
        raise HTTPException(status_code=400, detail="پلن نامعتبر")

    base_url = str(request.base_url).rstrip("/")

    data = {
        "merchant_id":  ZARINPAL_MERCHANT,
        "amount":       plan["price"],
        "description":  f"خرید اشتراک {plan['name']} - {customer.name}",
        "callback_url": f"{base_url}/payment/verify",
        "metadata":     {"mobile": customer.phone}
    }

    try:
        res  = requests.post(ZARINPAL_REQUEST, json=data, timeout=10)
        resp = res.json()

        if resp["data"]["code"] == 100:
            authority = resp["data"]["authority"]

            payment = Payment(
                customer_id = customer.id,
                amount      = plan["price"],
                plan        = req.plan,
                status      = "pending",
                ref_id      = authority
            )
            db.add(payment)
            db.commit()

            return {
                "success":     True,
                "payment_url": f"{ZARINPAL_START}{authority}",
                "amount":      plan["price"],
                "plan":        plan["name"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="خطا در ایجاد پرداخت"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verify")
async def payment_verify(
    Authority: str,
    Status:    str,
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(
        Payment.ref_id == Authority
    ).first()

    if not payment:
        return {"success": False, "message": "پرداخت پیدا نشد"}

    if Status != "OK":
        payment.status = "failed"
        db.commit()
        return {"success": False, "message": "پرداخت لغو شد"}

    data = {
        "merchant_id": ZARINPAL_MERCHANT,
        "amount":      payment.amount,
        "authority":   Authority
    }

    try:
        res  = requests.post(ZARINPAL_VERIFY, json=data, timeout=10)
        resp = res.json()

        if resp["data"]["code"] in [100, 101]:
            ref_id           = resp["data"]["ref_id"]
            payment.status   = "success"
            payment.ref_id   = str(ref_id)

            customer = payment.customer
            plan     = PLANS.get(payment.plan, {})
            days     = plan.get("days", 30)
            now      = datetime.now()

            customer.plan      = payment.plan
            customer.is_active = True
            if customer.expires_at and customer.expires_at > now:
                customer.expires_at += timedelta(days=days)
            else:
                customer.expires_at = now + timedelta(days=days)

            db.commit()

            return {
                "success": True,
                "message": f"پرداخت موفق! کد: {ref_id}",
                "ref_id":  ref_id
            }
        else:
            payment.status = "failed"
            db.commit()
            return {"success": False, "message": "تایید ناموفق"}

    except Exception as e:
        return {"success": False, "message": str(e)}
