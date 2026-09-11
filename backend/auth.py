from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db
import os
import secrets

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # در production حتماً SECRET_KEY را در env تنظیم کنید
    SECRET_KEY = secrets.token_hex(32)
    print("⚠️ SECRET_KEY از env خوانده نشد — یک کلید موقت ساخته شد (با ری‌استارت توکن‌ها باطل می‌شوند)")

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict, expires_hours: int = 24) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=expires_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return {}

def get_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db)
):
    payload = decode_token(credentials.credentials)
    if not payload.get("admin"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="دسترسی غیرمجاز"
        )
    return payload

def get_customer(api_key: str, db: Session):
    """اعتبارسنجی api_key + فعال بودن + انقضای اشتراک"""
    from backend.models import Customer
    if not api_key or not api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key الزامی است"
        )

    customer = db.query(Customer).filter(
        Customer.api_key == api_key.strip(),
        Customer.is_active == True
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key نامعتبر یا غیرفعال"
        )

    if customer.expires_at and customer.expires_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="اشتراک منقضی شده. لطفاً پلن خود را تمدید کنید."
        )

    return customer

def generate_api_key() -> str:
    return f"eai_{secrets.token_urlsafe(32)}"
