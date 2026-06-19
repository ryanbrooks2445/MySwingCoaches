from __future__ import annotations

import logging

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.job_runner import drain_jobs
from app.pipeline import run_analysis
from app.schemas import AnalyzeRequest, CoachingReportSchema
from app.trace_log import log_trace

logging.basicConfig(level=logging.INFO)
logging.getLogger("swing.trace").setLevel(logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

if settings.sentry_dsn:
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
    except ImportError:
        logger.warning("SENTRY_DSN is configured but sentry-sdk is not installed")

app = FastAPI(
    title="MySwingCoaches Analysis Service",
    description="OpenCV frame extraction + Gemini video coaching pipeline",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
    if settings.analysis_service_secret and x_analysis_secret != settings.analysis_service_secret:
        raise HTTPException(status_code=401, detail="Invalid analysis service secret")

    log_trace(
        "analysis_request_received",
        trace_id=request.trace_id,
        user_id=request.user_id,
        report_id=request.analysis_id,
        status="received",
        video_id=request.video_id,
    )
    logger.info("Starting analysis %s for video %s", request.analysis_id, request.video_id)
    return run_analysis(request)


@app.post("/jobs/drain")
def jobs_drain(
    x_analysis_secret: str | None = Header(default=None),
    limit: int = Query(default=1, ge=1, le=10),
):
    if settings.analysis_service_secret and x_analysis_secret != settings.analysis_service_secret:
        raise HTTPException(status_code=401, detail="Invalid analysis service secret")
    return drain_jobs(limit)
