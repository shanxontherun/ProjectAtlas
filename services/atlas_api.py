"""
Atlas Core API — FastAPI application entry point.

Exposes health, categories, and jobs endpoints for Project Atlas.
"""

from __future__ import annotations

import sqlite3
import logging

from typing import Any, Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from database import (
    claim_next_pending_job,
    create_job,
    fetch_all_categories,
    update_job_status,
    insert_research_product,
    fetch_all_research_products,
    product_exists,
    create_product_registry_entry,
    touch_product,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Atlas Core API",
    description="Core HTTP API for Project Atlas",
    version="0.1.0",
)


class JobCreateRequest(BaseModel):
    """Request body for creating a new job."""

    department: str = Field(..., min_length=1, description="Owning department name")
    job_type: str = Field(..., min_length=1, description="Job type identifier")
    priority: int = Field(default=5, ge=1, description="Higher values run sooner")
    payload: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured payload stored as JSON text",
    )


class JobCreateResponse(BaseModel):
    """Response returned after a successful job insert."""

    success: bool
    job_id: int


class JobNextResponse(BaseModel):
    """Response returned when a PENDING job is claimed for work."""

    job_id: int
    department: str
    job_type: str
    priority: int
    payload: Any
    status: str


class JobUpdateRequest(BaseModel):
    """Request body for updating a job's terminal status."""

    status: Literal["COMPLETED", "FAILED", "CANCELLED"] = Field(
        ...,
        description="New job status",
    )
    error_message: str | None = Field(
        default=None,
        description="Optional failure detail stored when status is FAILED",
    )


class JobUpdateResponse(BaseModel):
    """Response returned after a successful job status update."""

    success: bool
    job_id: int
    status: str



class ResearchProductCreate(BaseModel):
    job_id: int
    category: str
    product_name: str
    product_url: str
    source: str = "Amazon"
    price: float | None = None
    currency: str = "USD"
    rating: float | None = None
    review_count: int | None = None
    image_url: str | None = None
    ai_summary: str | None = None


class ResearchProductResponse(BaseModel):
    success: bool
    research_product_id: int


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check used by local tooling and orchestrators."""
    return {
        "status": "ok",
        "service": "Atlas Core API",
    }


@app.get("/categories")
def get_categories() -> list[dict[str, Any]]:
    """Return all categories from the Atlas SQLite database."""
    try:
        return fetch_all_categories()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        # Surface unexpected DB failures without leaking stack traces to clients
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch categories: {exc}",
        ) from exc


@app.post(
    "/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_job(body: JobCreateRequest) -> JobCreateResponse:
    """Create a new job row and return its generated job_id."""
    try:
        logger.info(
    "Creating job: department=%s job_type=%s priority=%s",
    body.department,
    body.job_type,
    body.priority,
)
        job_id = create_job(
            department=body.department,
            job_type=body.job_type,
            priority=body.priority,
            payload=body.payload,
        )
        logger.info("Job created successfully: job_id=%s", job_id)
        
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create job: {exc}",
        ) from exc

    return JobCreateResponse(success=True, job_id=job_id)


@app.get("/jobs/next", response_model=JobNextResponse)
def get_next_job() -> JobNextResponse:
    """
    Claim the oldest PENDING job and mark it IN_PROGRESS.

    Returns 404 when the pending queue is empty.
    """
    try:
        job = claim_next_pending_job()
        logger.info("Claimed job: %s", job["job_id"] if job else "None")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to claim next job: {exc}",
        ) from exc

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending jobs.",
        )

    return JobNextResponse(**job)


@app.patch("/jobs/{job_id}", response_model=JobUpdateResponse)
def patch_job(job_id: int, body: JobUpdateRequest) -> JobUpdateResponse:
    """
    Update a job's status (e.g. COMPLETED / FAILED) and set completed_at.

    Returns 404 when the job_id does not exist.
    """
    try:
        updated = update_job_status(
            job_id=job_id,
            new_status=body.status,
            error_message=body.error_message,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update job: {exc}",
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found.",
        )

    return JobUpdateResponse(
        success=True,
        job_id=updated["job_id"],
        status=updated["status"],
    )


@app.post(
    "/research-products",
    response_model=ResearchProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_research_product(body: ResearchProductCreate) -> ResearchProductResponse:

    # For now we use the product URL as the unique product key.
    # Later we'll replace this with the Amazon ASIN.
    product_key = body.product_url

    if product_exists(product_key):
        touch_product(
            product_key=product_key,
            last_job_id=body.job_id,
        )
    else:
        create_product_registry_entry(
            product_key=product_key,
            product_url=body.product_url,
            product_name=body.product_name,
            category=body.category,
            source=body.source,
            last_job_id=body.job_id,
        )

    research_product_id = insert_research_product(
        job_id=body.job_id,
        category=body.category,
        product_name=body.product_name,
        product_url=body.product_url,
        source=body.source,
        price=body.price,
        currency=body.currency,
        rating=body.rating,
        review_count=body.review_count,
        image_url=body.image_url,
        ai_summary=body.ai_summary,
    )

    logger.info("Inserted research product: %s", research_product_id)

    return ResearchProductResponse(
        success=True,
        research_product_id=research_product_id,
    )


@app.get("/research-products")
def get_research_products():
    return fetch_all_research_products()
