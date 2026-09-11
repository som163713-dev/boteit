from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.models import Admin, Customer, Message, Payment
from backend.auth import (
    hash_password, verify_password,
    create_token, get_admin, generate_api_key
)
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class CustomerCreate(BaseModel):
    name:     str
    business: str
    phone:    str
    category: str
    plan:     str = "basic"
    days:     int = 30


class CustomerUpdate(BaseModel):
    is_active: bool = True
    plan:      str  = "basic"
    days:      int  = 30


@router.post("/setup")
async def setup(req: LoginRequest, db: Session = Depends(get_db)):
    """ساخت ادمین اول (فقط یک‌بار)"""
    try:
        exists = db.query(Admin).first()
        if exists:
            raise HTTPException(status_code=400, detail="ادمین قبلاً ساخته شده")

        admin = Admin(
            username=req.username,
            password=hash_password(req.password)
        )
        db.add(admin)
        db.commit()
        return {"message": "ادمین ساخته شد ✅"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Setup Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    try:
        admin = db.query(Admin).filter(Admin.username == req.username).first()
        if not admin or not verify_password(req.password, admin.password):
            raise HTTPException(status_code=401, detail="نام کاربری یا رمز اشتباهه")

        token = create_token({"admin": True, "username": req.username})
        return {"token": token, "username": req.username}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):
    try:
        admin_user = db.query(Admin).filter(Admin.username == admin["username"]).first()
        if not admin_user:
            raise HTTPException(status_code=404, detail="ادمین پیدا نشد")

        if not verify_password(req.old_password, admin_user.password):
            raise HTTPException(status_code=400, detail="رمز قدیمی اشتباهه!")

        if len(req.new_password) < 6:
            raise HTTPException(status_code=400, detail="رمز جدید باید حداقل ۶ کاراکتر باشه!")

        admin_user.password = hash_password(req.new_password)
        db.commit()
        return {"message": "رمز عبور تغییر کرد ✅"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers")
async def get_customers(admin=Depends(get_admin), db: Session = Depends(get_db)):
    customers = db.query(Customer).order_by(Customer.id.desc()).all()
    return [{
        "id":         c.id,
        "name":       c.name,
        "business":   c.business,
        "phone":      c.phone,
        "category":   c.category,
        "plan":       c.plan,
        "is_active":  c.is_active,
        "api_key":    c.api_key,
        "expires_at": str(c.expires_at) if c.expires_at else None,
        "created_at": str(c.created_at),
        "msg_count":  len(c.messages),
    } for c in customers]


@router.post("/customers")
async def add_customer(
    req: CustomerCreate,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):
    try:
        exists = db.query(Customer).filter(Customer.phone == req.phone).first()
        if exists:
            raise HTTPException(status_code=400, detail="این شماره قبلاً ثبت شده")

        customer = Customer(
            name=req.name,
            business=req.business,
            phone=req.phone,
            category=req.category,
            plan=req.plan,
            api_key=generate_api_key(),
            expires_at=datetime.now() + timedelta(days=req.days),
            is_active=True,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        return {
            "message":  "مشتری اضافه شد ✅",
            "api_key":  customer.api_key,
            "customer": customer.name,
            "miniapp_link_hint": f"/?key={customer.api_key}",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/customers/{customer_id}")
async def update_customer(
    customer_id: int,
    req: CustomerUpdate,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="مشتری پیدا نشد")

        customer.is_active = req.is_active
        customer.plan = req.plan
        customer.expires_at = datetime.now() + timedelta(days=req.days)
        db.commit()
        return {"message": "مشتری آپدیت شد ✅"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: int,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="مشتری پیدا نشد")
        db.delete(customer)
        db.commit()
        return {"message": "مشتری حذف شد ✅"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
