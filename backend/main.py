from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import os

app = FastAPI(title="Eitaa AI Miniapp", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routes.chat    import router as chat_router
from backend.routes.admin   import router as admin_router
from backend.routes.stats   import router as stats_router
from backend.routes.payment import router as payment_router
from backend.database       import init_db
from backend.keepalive      import start_keep_alive

app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(stats_router)
app.include_router(payment_router)

app.mount("/static",      StaticFiles(directory="frontend"),       name="static")
app.mount("/admin-panel", StaticFiles(directory="frontend/admin"), name="admin")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.head("/")
async def root_head():
    return Response(status_code=200)

@app.get("/panel")
async def admin_panel():
    return FileResponse("frontend/admin/index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

@app.on_event("startup")
async def startup():
    init_db()
    start_keep_alive()
    print("🚀 سرور Enterprise شروع به کار کرد!")
