#!/usr/bin/env python3
"""
Laya Fast System 1 Decision Engine - Web Server & REST API
Built with FastAPI and modern interactive UI.
"""

import time
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Check PyTorch & Laya
try:
    import torch
    from laya import Router
    LAYA_AVAILABLE = True
except ImportError:
    LAYA_AVAILABLE = False
    Router = None

app = FastAPI(
    title="Laya System 1 Decision Engine Demo",
    description="High-speed non-autoregressive decision model playground",
    version="1.0.0"
)

# Static & Templates setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Global Router Instance
router_instance: Optional[Any] = None
device_name: str = "cpu"


@app.on_event("startup")
def startup_event():
    global router_instance, device_name
    if LAYA_AVAILABLE:
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[Laya Startup] Initializing Router on device: {device_name.upper()}")
        try:
            router_instance = Router(preload=True, device=device_name)
            print("[Laya Startup] Models successfully preloaded!")
        except Exception as e:
            print(f"[Laya Startup Warning] Router initialization failed: {e}")
            router_instance = None
    else:
        print("[Laya Startup Warning] Laya is not installed yet.")


class PredictRequest(BaseModel):
    state: Dict[str, Any] = Field(..., example={"body": "I was charged twice on my credit card."})
    questions: Dict[str, Any] = Field(..., example={
        "intent": {"type": "choice", "options": ["refund", "cancellation", "support"]},
        "is_urgent": {"type": "noul"}
    })


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "device": device_name,
            "is_laya_ready": router_instance is not None
        }
    )


@app.get("/api/status")
async def get_status():
    cuda_available = torch.cuda.is_available() if LAYA_AVAILABLE else False
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else None
    return {
        "laya_ready": router_instance is not None,
        "device": device_name,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "architecture": "ModernBERT-large Non-Autoregressive Decision Head"
    }


@app.post("/api/predict")
async def predict_endpoint(req: PredictRequest):
    if router_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Laya router is not ready or failed to initialize."
        )

    t0 = time.perf_counter()
    try:
        result = router_instance.predict(req.state, req.questions)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        
        return {
            "success": True,
            "latency_ms": round(latency_ms, 2),
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/benchmark")
async def benchmark_endpoint(iterations: int = 10):
    if router_instance is None:
        raise HTTPException(status_code=503, detail="Laya router not ready.")

    state = {"text": "Subscription renewal failed, need urgent invoice copy."}
    questions = {
        "intent": {"type": "choice", "options": ["billing", "tech_support", "sales"]},
        "urgent": {"type": "noul"}
    }

    latencies = []
    for _ in range(max(1, min(iterations, 50))):
        t0 = time.perf_counter()
        _ = router_instance.predict(state, questions)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    return {
        "iterations": len(latencies),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "avg_ms": round(sum(latencies) / len(latencies), 2),
        "p95_ms": round(sorted(latencies)[int(0.95 * len(latencies))], 2),
        "device": device_name
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
