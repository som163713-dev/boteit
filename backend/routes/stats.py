from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models import Customer, Message, Payment
from backend.auth import get_admin
from datetime import datetime, timedelta

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/dashboard")
async def dashboard(
    admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    try:
        now   = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_customers  = db.query(Customer).count()
        active_customers = db.query(Customer).filter(
            Customer.is_active == True
        ).count()

        total_messages = db.query(Message).count()
        today_messages = db.query(Message).filter(
            Message.created_at >= today
        ).count()

        total_revenue = db.query(
            func.sum(Payment.amount)
        ).filter(Payment.status == "success").scalar() or 0

        month_revenue = db.query(
            func.sum(Payment.amount)
        ).filter(
            Payment.status == "success",
            Payment.created_at >= now.replace(day=1, hour=0,
                                              minute=0, second=0)
        ).scalar() or 0

        weekly_msgs = []
        for i in range(7):
            day_start = today - timedelta(days=i)
            day_end   = day_start + timedelta(days=1)
            count     = db.query(Message).filter(
                Message.created_at >= day_start,
                Message.created_at <  day_end
            ).count()
            weekly_msgs.append({
                "date":  day_start.strftime("%m/%d"),
                "count": count
            })

        categories = db.query(
            Message.category,
            func.count(Message.id).label("count")
        ).group_by(Message.category).all()

        top_customers = db.query(
            Customer.name,
            Customer.business,
            func.count(Message.id).label("msg_count")
        ).join(Message).group_by(Customer.id)\
         .order_by(func.count(Message.id).desc())\
         .limit(5).all()

        return {
            "overview": {
                "total_customers":  total_customers,
                "active_customers": active_customers,
                "total_messages":   total_messages,
                "today_messages":   today_messages,
                "total_revenue":    total_revenue,
                "month_revenue":    month_revenue
            },
            "weekly_messages": list(reversed(weekly_msgs)),
            "categories": [
                {"name": c[0], "count": c[1]}
                for c in categories
            ],
            "top_customers": [
                {
                    "name":      tc[0],
                    "business":  tc[1],
                    "msg_count": tc[2]
                }
                for tc in top_customers
            ]
        }

    except Exception as e:
        print(f"❌ Stats Error: {e}")
        return {"error": str(e)}
