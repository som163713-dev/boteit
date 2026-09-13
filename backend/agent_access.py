"""
کاتالوگ ایجنت‌ها + منطق دسترسی.
هر ایجنت یه کلید ثابت داره (مثلاً "content"). این ماژول تصمیم می‌گیره
کدوم مشتری به کدوم ایجنت دسترسی داره: یا از روی پیش‌فرض پلنش، یا از روی
override دستیِ ادمین (که می‌تونه هم محدودش کنه هم بهش «هدیه» بده).
"""
import json

# ── کاتالوگ ایجنت‌های فعلاً پیاده‌سازی‌شده ──────────────────────────
AGENT_CATALOG = {
    "content": {
        "name": "✍️ تولید محتوا",
        "description": "کپشن و متن تبلیغاتی آماده‌ی انتشار می‌سازه.",
    },
    "campaign": {
        "name": "📣 طرح کمپین",
        "description": "بر اساس آمار واقعی تعامل، طرح کمپین دو هفته‌ای می‌سازه.",
    },
    "report": {
        "name": "📊 گزارش تحلیلی",
        "description": "گزارش واقعی رشد/افت تعامل کاربرها با ربات رو می‌ده.",
    },
}

# ── پیش‌فرض هر پلن (اگه ادمین دستی override نکرده باشه) ──────────────
PLAN_DEFAULTS = {
    "basic":      ["content"],
    "pro":        ["content", "campaign"],
    "enterprise": ["content", "campaign", "report"],
}


def get_enabled_agents(customer) -> list[str]:
    """
    اگه ادمین دستی برای این مشتری چیزی ست کرده باشه (enabled_agents پر باشه)،
    همون قطعی و نهاییه — چه برای محدودکردن، چه برای هدیه دادن ایجنت اضافه.
    وگرنه پیش‌فرض پلن فعلیش اعمال می‌شه.
    """
    if customer.enabled_agents:
        try:
            return json.loads(customer.enabled_agents)
        except (json.JSONDecodeError, TypeError):
            pass
    return PLAN_DEFAULTS.get(customer.plan, PLAN_DEFAULTS["basic"])


def is_agent_enabled(customer, agent_key: str) -> bool:
    return agent_key in get_enabled_agents(customer)


def set_enabled_agents(customer, agent_keys: list[str]):
    """ست کردن دستیِ ادمین — این از این به بعد به پیش‌فرض پلن اولویت داره."""
    valid = [k for k in agent_keys if k in AGENT_CATALOG]
    customer.enabled_agents = json.dumps(valid, ensure_ascii=False)


def reset_to_plan_default(customer):
    """برگردوندن مشتری به پیش‌فرض پلنش (پاک کردن override دستی)."""
    customer.enabled_agents = None


def catalog_with_status(customer) -> list[dict]:
    enabled = set(get_enabled_agents(customer))
    return [
        {"key": key, "name": info["name"], "description": info["description"],
         "enabled": key in enabled}
        for key, info in AGENT_CATALOG.items()
    ]
