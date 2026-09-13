from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./eitaa_ai.db"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _migrate_add_missing_columns():
    """
    create_all() جدول‌های جدید رو می‌سازه ولی به جدول‌های موجود ستون اضافه
    نمی‌کنه. این تابع فقط ستون‌های جدیدی که به مدل‌های موجود اضافه شدن رو
    (اگه از قبل نباشن) با ALTER TABLE اضافه می‌کنه — روی SQLite و Postgres
    هر دو کار می‌کنه. اگه ستون از قبل وجود داشته باشه، هیچ کاری انجام نمی‌ده.
    """
    inspector = inspect(engine)
    existing_columns = {col["name"] for col in inspector.get_columns("customers")}

    if "enabled_agents" not in existing_columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE customers ADD COLUMN enabled_agents TEXT"))
            conn.commit()
        print("✅ ستون enabled_agents به جدول customers اضافه شد.")

def init_db():
    from backend.models import Customer, Message, Payment, Admin, ContentItem
    Base.metadata.create_all(bind=engine)
    _migrate_add_missing_columns()
    print("✅ دیتابیس آماده شد!")
