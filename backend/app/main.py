import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import zones, predict, alerts, reports, admin
from .storage import get_storage
from .services.risk_engine import evaluate_all_zones
from .ml.predict import _load_model
from .ml import train_model as train_model_module

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.exists(train_model_module.MODEL_PATH):
        print("[startup] No trained model found, training one now...")
        train_model_module.train_and_save()
    _load_model()

    storage = get_storage()
    evaluate_all_zones(storage)
    print(f"[startup] AquaAlert Odisha backend ready. Storage mode: {storage.mode}")
    yield


app = FastAPI(title="AquaAlert Odisha API", lifespan=lifespan)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(zones.router)
app.include_router(predict.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    storage = get_storage()
    return {"status": "ok", "storage_mode": storage.mode}
