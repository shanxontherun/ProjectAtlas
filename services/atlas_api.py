"""
Atlas Core API — FastAPI application entry point.

Exposes health, categories, and jobs endpoints for Project Atlas.
"""

from __future__ import annotations

import sqlite3
import sys
import logging

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Ensure the workspace root is importable so services can be referenced
# as a package whether uvicorn runs from services/ or the repo root.
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

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
from services.ai_service import (
    AIValidationError,
    AlreadyGeneratedError,
    generate_and_save_ai_content,
    regenerate_and_save_ai_content,
)
from services.database import (
    ai_content_exists,
    approve_ai_content,
    fetch_ai_content,
    fetch_research_product_by_id,
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


class AiContentGenerateRequest(BaseModel):
    """Request body for generating AI content for a research product."""

    research_product_id: int = Field(
        ...,
        ge=1,
        description="Research product to generate content for",
    )


class AiContentApproveRequest(BaseModel):
    """Request body for approving AI content for a research product."""

    research_product_id: int = Field(
        ...,
        ge=1,
        description="Research product whose content should be approved",
    )


class AiContentActionResponse(BaseModel):
    """Response returned after a generate / approve action."""

    success: bool
    ai_content_id: int | None = None
    content: dict[str, Any] | None = None


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
    try:
        return fetch_all_research_products()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        # Surface unexpected DB failures without leaking stack traces to clients
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch research products: {exc}",
        ) from exc


@app.get("/ai-content")
def get_ai_content():
    """
    Return every research product with its generated AI content (if any).

    Reuses the enriched fetch_ai_content query; waiting products have a
    NULL ai_content_id so the AI Studio queue can render them as "waiting".
    """
    try:
        return fetch_ai_content()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch AI content: {exc}",
        ) from exc


@app.post(
    "/ai-content/generate",
    response_model=AiContentActionResponse,
)
def generate_ai_content_for_product(
    body: AiContentGenerateRequest,
) -> AiContentActionResponse:
    """
    Generate (or regenerate) and persist AI content for a research product.

    Reuses the existing AI generation + persistence service that the AI
    worker calls. Manual regeneration is an upsert: when content already
    exists the existing ai_content row is updated in place (replace, never
    append, never a duplicate row); when no content exists a new row is
    created. The worker path stays idempotent — it calls
    generate_and_save_ai_content directly, which skips existing content.
    """
    try:
        product = fetch_research_product_by_id(body.research_product_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research product {body.research_product_id} not found.",
        )

    try:
        if ai_content_exists(body.research_product_id):
            ai_content_id = regenerate_and_save_ai_content(product)
        else:
            ai_content_id = generate_and_save_ai_content(product)

        rows = fetch_ai_content(body.research_product_id)
        updated = rows[0] if rows else None
    except AlreadyGeneratedError:
        logger.info(
            "AI content already exists for product %s; skipping.",
            body.research_product_id,
        )
        try:
            rows = fetch_ai_content(body.research_product_id)
            updated = rows[0] if rows else None
        except Exception:
            updated = None
        return AiContentActionResponse(
            success=True,
            ai_content_id=None,
            content=updated,
        )
    except AIValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"AI generation failed validation: {exc}",
        ) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist AI content: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI generation failed: {exc}",
        ) from exc

    logger.info(
        "Generated AI content for product %s (ai_content_id=%s)",
        body.research_product_id,
        ai_content_id,
    )

    return AiContentActionResponse(
        success=True,
        ai_content_id=ai_content_id,
        content=updated,
    )


@app.post(
    "/ai-content/approve",
    response_model=AiContentActionResponse,
)
def approve_ai_content_for_product(
    body: AiContentApproveRequest,
) -> AiContentActionResponse:
    """
    Approve the AI content of a research product.

    Reuses the existing ai_content.status field
    (GENERATED / APPROVED / REJECTED) via approve_ai_content.
    """
    try:
        ai_content_id = approve_ai_content(body.research_product_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve AI content: {exc}",
        ) from exc

    if ai_content_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No AI content exists for research product "
                f"{body.research_product_id}."
            ),
        )

    logger.info(
        "Approved AI content %s (research product %s)",
        ai_content_id,
        body.research_product_id,
    )

    return AiContentActionResponse(success=True, ai_content_id=ai_content_id)
