from __future__ import annotations

import logging

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.pipeline import run_analysis
from app.schemas import AnalyzeRequest, CoachingReportSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MySwingCoaches Analysis Service",
    description="OpenCV frame extraction + Gemini video coaching pipeline",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "analysis-service"}


@app.post("/analyze", response_model=CoachingReportSchema)
def analyze(
    request: AnalyzeRequest,
    x_analysis_secret: str | None = Header(default=None),
):
    settings = get_settings()
    if settings.analysis_service_secret and x_analysis_secret != settings.analysis_service_secret:
        raise HTTPException(status_code=401, detail="Invalid analysis service secret")

    logger.info("Starting analysis %s for video %s", request.analysis_id, request.video_id)
    return run_analysis(request)
