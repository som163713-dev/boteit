from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, JSONResponse
import os

# مسیر ریشه پروژه (یک سطح بالاتر از backend/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
ADMIN_DIR = os.path.join(FRONTEND_DIR, "admin")

app = FastAPI(title="Eitaa AI Miniapp", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routes.chat import router as chat_router
from backend.routes.admin import router as admin_router
from backend.routes.stats import router as stats_router
from backend.routes.payment import router as payment_router
from backend.routes.factory import router as factory_router
from backend.database import init_db
from backend.keepalive import start_keep_alive

app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(stats_router)
app.include_router(payment_router)
app.include_router(factory_router)

# فقط اگر پوشه وجود داشت mount کن تا سرور کرش نکند
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
else:
    print(f"⚠️ پوشه frontend پیدا نشد: {FRONTEND_DIR}")

if os.path.isdir(ADMIN_DIR):
    app.mount("/admin-panel", StaticFiles(directory=ADMIN_DIR), name="admin")


@app.get("/")
async def root():
    index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return JSONResponse(
        {"error": "frontend/index.html پیدا نشد", "base": BASE_DIR},
        status_code=500,
    )


@app.head("/")
async def root_head():
    return Response(status_code=200)


@app.get("/panel")
async def admin_panel():
    panel = os.path.join(ADMIN_DIR, "index.html")
    if os.path.isfile(panel):
        return FileResponse(panel)
    return JSONResponse({"error": "admin panel not found"}, status_code=404)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "3.1.0",
        "frontend_exists": os.path.isdir(FRONTEND_DIR),
    }


@app.on_event("startup")
async def startup():
    init_db()
    start_keep_alive()
    print(f"🚀 سرور شروع شد | BASE={BASE_DIR} | frontend={os.path.isdir(FRONTEND_DIR)}")
