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
from fastapi.responses import FileResponse
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
from services.creative_service import (
    CreativeContentNotFoundError,
    CreativeLockedError,
    approve_creative_for_product,
    fetch_creative_image_path,
    fetch_creatives_workflow,
    generate_and_save_creative,
    reopen_creative_for_review,
    save_creative_presentation,
)
from services.database import (
    ai_content_exists,
    approve_ai_content,
    fetch_ai_content,
    fetch_research_product_by_id,
)
from services.pinterest_accounts import (
    fetch_active_accounts,
)
from services.pinterest_boards import (
    fetch_active_boards,
)
from services.category_routes import (
    fetch_routes_by_category,
)
from services.pinterest_client import publish_pin
from services.queue_service import (
    create_queue_item,
    fetch_active_queue_by_ai_content,
    find_cancelled_queue_item,
    fetch_publishing_rows,
    fetch_publishing_summary,
    fetch_queue_item_details,
    mark_queue_cancelled,
    mark_queue_failed,
    mark_queue_published,
    mark_queue_scheduled,
    reactivate_queue_item,
    update_queue_board,
)
from services.creative_service import queue_creative_for_publishing
from services.creative_service import unqueue_creative_from_publishing

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


class CreativePresentation(BaseModel):
    """
    Presentation state persisted with a creative.

    ``headline`` and the property overrides are optional; the backend
    merges only the provided fields so callers can send the full Studio
    state (template, variant, headline, CTA, brand, logo position,
    overlay style) without clobbering untouched fields.
    """

    selected_template: str | None = Field(
        default=None,
        description="Template selection (e.g. minimal, luxury, lifestyle)",
    )
    selected_variant: str | None = Field(
        default=None,
        description="Variant selection (a, b, c, d)",
    )
    headline: str | None = Field(
        default=None,
        description="Headline override persisted with the creative",
    )
    cta: str | None = Field(
        default=None,
        description="Call-to-action override",
    )
    brand: str | None = Field(
        default=None,
        description="Brand override",
    )
    logo_position: str | None = Field(
        default=None,
        description="Logo position override",
    )
    overlay_style: str | None = Field(
        default=None,
        description="Overlay style override",
    )


def _presentation_kwargs(
    presentation: CreativePresentation | None,
) -> dict[str, Any]:
    """
    Convert an API presentation payload into service-layer arguments.

    Flattens the property overrides into the ``properties`` dict the
    service persists as JSON alongside the template and variant.
    """

    if presentation is None:
        return {}

    properties: dict[str, Any] = {}

    if presentation.cta is not None:
        properties["cta"] = presentation.cta
    if presentation.brand is not None:
        properties["brand"] = presentation.brand
    if presentation.logo_position is not None:
        properties["logoPosition"] = presentation.logo_position
    if presentation.overlay_style is not None:
        properties["overlayStyle"] = presentation.overlay_style

    return {
        "selected_template": presentation.selected_template,
        "selected_variant": presentation.selected_variant,
        "headline": presentation.headline,
        "properties": properties or None,
    }


class CreativeGenerateRequest(BaseModel):
    """Request body for generating a creative for a research product."""

    research_product_id: int = Field(
        ...,
        ge=1,
        description="Research product whose creative should be generated",
    )
    presentation: CreativePresentation | None = Field(
        default=None,
        description="Presentation state to persist with the generated creative",
    )


class CreativeApproveRequest(BaseModel):
    """Request body for approving a creative for a research product."""

    research_product_id: int = Field(
        ...,
        ge=1,
        description="Research product whose creative should be approved",
    )
    presentation: CreativePresentation | None = Field(
        default=None,
        description="Presentation state to persist with the approved creative",
    )


class CreativeSaveRequest(BaseModel):
    """Request body for persisting Creative Studio presentation edits."""

    research_product_id: int = Field(
        ...,
        ge=1,
        description="Research product whose creative should be saved",
    )
    presentation: CreativePresentation = Field(
        ...,
        description="Presentation state to persist with the creative",
    )


class CreativeReopenRequest(BaseModel):
    """Request body for returning an approved creative to review."""

    research_product_id: int = Field(
        ...,
        ge=1,
        description="Research product whose creative should be reopened",
    )


class CreativeActionResponse(BaseModel):
    """Response returned after a creative generate / approve action."""

    success: bool
    creative_id: int | None = None
    content: dict[str, Any] | None = None


class PublishingQueueRequest(BaseModel):
    """Request body for moving an approved creative into the queue."""

    research_product_id: int = Field(
        ...,
        ge=1,
        description="Research product whose approved creative should be queued",
    )


class PublishingRemoveRequest(BaseModel):
    """Request body for removing a queued creative from publishing."""

    research_product_id: int = Field(
        ...,
        ge=1,
        description="Research product whose queued creative should be removed",
    )
    pin_id: int | None = Field(
        default=None,
        description="Queue item to cancel; when omitted the active item is used",
    )


class PublishingScheduleRequest(BaseModel):
    """Request body for scheduling a queued pin."""

    pin_id: int = Field(
        ...,
        ge=1,
        description="Queue item to schedule",
    )
    scheduled_at: str = Field(
        ...,
        description="ISO-8601 datetime when the pin should publish",
    )


class PublishingPublishNowRequest(BaseModel):
    """Request body for publishing a queued pin immediately."""

    pin_id: int = Field(
        ...,
        ge=1,
        description="Queue item to publish",
    )


class PublishingBoardRequest(BaseModel):
    """Request body for changing a queued pin's board and account."""

    pin_id: int = Field(
        ...,
        ge=1,
        description="Queue item whose board should change",
    )
    account_id: int = Field(
        ...,
        ge=1,
        description="Pinterest account the pin should publish to",
    )
    board_id: int = Field(
        ...,
        ge=1,
        description="Pinterest board the pin should publish to",
    )


class PublishingActionResponse(BaseModel):
    """Response returned after a publishing action."""

    success: bool
    pin_id: int | None = None
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


@app.get("/creatives")
def get_creatives():
    """
    Return every research product with its AI content and creative (if any).

    Reuses the enriched fetch_creatives_workflow query; waiting items
    have a NULL creative_id so the Creative Studio queue can render
    them as "waiting" alongside generated and approved ones.
    """
    try:
        return fetch_creatives_workflow()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch creatives: {exc}",
        ) from exc


@app.post(
    "/creatives/generate",
    response_model=CreativeActionResponse,
)
def generate_creative_for_product(
    body: CreativeGenerateRequest,
) -> CreativeActionResponse:
    """
    Generate (or retry) and persist a creative for a research product.

    Reuses the same creative generation pipeline as the creative worker
    (image resolution, content mapping, RenderingEngine). The action is
    idempotent: an existing creative is returned unchanged and never
    rendered twice; a FAILED creative is replaced so manual retry
    works. The worker batch path stays untouched and idempotent.
    """
    try:
        creative = generate_and_save_creative(
            body.research_product_id,
            **_presentation_kwargs(body.presentation),
        )
    except CreativeContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist creative: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Creative generation failed: {exc}",
        ) from exc

    creative_id = int(creative["creative_id"])

    rows = fetch_creatives_workflow(body.research_product_id)
    updated = rows[0] if rows else None

    logger.info(
        "Generated creative %s for research product %s",
        creative_id,
        body.research_product_id,
    )

    return CreativeActionResponse(
        success=True,
        creative_id=creative_id,
        content=updated,
    )


@app.post(
    "/creatives/approve",
    response_model=CreativeActionResponse,
)
def approve_creative_for_product_endpoint(
    body: CreativeApproveRequest,
) -> CreativeActionResponse:
    """
    Approve the creative of a research product.

    Reuses the existing creative_assets.status field
    (GENERATED / APPROVED / FAILED) via mark_creative_approved.
    """
    try:
        creative_id = approve_creative_for_product(
            body.research_product_id,
            **_presentation_kwargs(body.presentation),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve creative: {exc}",
        ) from exc

    if creative_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No creative exists for research product "
                f"{body.research_product_id}."
            ),
        )

    rows = fetch_creatives_workflow(body.research_product_id)
    updated = rows[0] if rows else None

    logger.info(
        "Approved creative %s (research product %s)",
        creative_id,
        body.research_product_id,
    )

    return CreativeActionResponse(
        success=True,
        creative_id=creative_id,
        content=updated,
    )


@app.post(
    "/creatives/save",
    response_model=CreativeActionResponse,
)
def save_creative_for_product(
    body: CreativeSaveRequest,
) -> CreativeActionResponse:
    """
    Persist Creative Studio presentation edits for a product's creative.

    Updates the selected template, variant, headline and lightweight
    properties without changing status, so the Studio restores exactly
    what was reviewed after a refresh. Approved and queued creatives
    are locked and reject edits here — the Studio disables editing for
    them, and this endpoint is the server-side backstop.
    """
    try:
        creative = save_creative_presentation(
            body.research_product_id,
            **_presentation_kwargs(body.presentation),
        )
    except CreativeLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save creative: {exc}",
        ) from exc

    if creative is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No creative exists for research product "
                f"{body.research_product_id}."
            ),
        )

    creative_id = int(creative["creative_id"])

    rows = fetch_creatives_workflow(body.research_product_id)
    updated = rows[0] if rows else None

    logger.info(
        "Saved presentation for creative %s (research product %s)",
        creative_id,
        body.research_product_id,
    )

    return CreativeActionResponse(
        success=True,
        creative_id=creative_id,
        content=updated,
    )


@app.get("/publishing")
def get_publishing():
    """
    Return the Publishing Center read model.

    Combines the active queue (PENDING / READY), the history
    (PUBLISHED / FAILED / CANCELLED), the summary counts and the
    available Pinterest accounts and boards into a single response so
    the Publishing Center renders from live data.
    """
    try:
        queue = fetch_publishing_rows(("PENDING", "READY"))
        history = fetch_publishing_rows(
            ("PUBLISHED", "FAILED", "CANCELLED"),
            real_accounts_only=True,
        )
        summary = fetch_publishing_summary()
        accounts = fetch_active_accounts()
        boards = fetch_active_boards()
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch publishing data: {exc}",
        ) from exc

    return {
        "queue": queue,
        "history": history,
        "summary": summary,
        "accounts": accounts,
        "boards": boards,
    }


@app.get("/publishing/accounts")
def get_publishing_accounts():
    """Return the active Pinterest accounts for the Publishing Center."""

    try:
        return fetch_active_accounts()
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch accounts: {exc}",
        ) from exc


@app.get("/publishing/boards")
def get_publishing_boards():
    """Return every active Pinterest board across all accounts."""

    try:
        return fetch_active_boards()
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch boards: {exc}",
        ) from exc


@app.post(
    "/publishing/queue",
    response_model=PublishingActionResponse,
)
def queue_creative_for_publishing_endpoint(
    body: PublishingQueueRequest,
) -> PublishingActionResponse:
    """
    Move an approved creative into the publishing queue.

    Resolves the destination account and board from the product's
    category route, persists the queue item (PENDING), then flips the
    creative to QUEUED so Creative Studio locks further edits.
    """
    product = fetch_research_product_by_id(body.research_product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No research product {body.research_product_id}.",
        )

    category = product.get("category")
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product has no category to route publishing.",
        )

    category_slug = category.lower().replace(" ", "_")
    routes = fetch_routes_by_category(category_slug)
    if not routes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No publishing route is configured for category "
                f"'{category}'. Add a category route in the database "
                "before queueing."
            ),
        )

    rows = fetch_creatives_workflow(body.research_product_id)
    workflow = rows[0] if rows else None
    if workflow is None or workflow.get("creative_id") is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No creative exists for research product "
            f"{body.research_product_id}.",
        )

    ai_content_id = workflow.get("ai_content_id")
    if ai_content_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No AI content is linked to this product's creative.",
        )

    active = fetch_active_queue_by_ai_content(ai_content_id)
    if active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Creative for product {body.research_product_id} is "
                "already in the publishing queue."
            ),
        )

    route = routes[0]

    try:
        cancelled = find_cancelled_queue_item(
            ai_content_id,
            route["account_id"],
            route["board_id"],
        )

        if cancelled is not None:
            pin_id = int(cancelled["pin_id"])
            reactivate_queue_item(pin_id)
        else:
            pin_id = create_queue_item(
                ai_content_id=ai_content_id,
                account_id=route["account_id"],
                board_id=route["board_id"],
                affiliate_url=product.get("product_url"),
                image_url=workflow.get("creative_image_path"),
                publish_order=route.get("priority", 1),
            )

        creative_id = queue_creative_for_publishing(
            body.research_product_id
        )
    except CreativeLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue creative: {exc}",
        ) from exc

    content = fetch_queue_item_details(pin_id)

    logger.info(
        "Queued creative %s (pin %s) for product %s",
        creative_id,
        pin_id,
        body.research_product_id,
    )

    return PublishingActionResponse(
        success=True,
        pin_id=pin_id,
        content=content,
    )


@app.post(
    "/publishing/remove",
    response_model=PublishingActionResponse,
)
def remove_queued_creative_endpoint(
    body: PublishingRemoveRequest,
) -> PublishingActionResponse:
    """
    Remove a creative from the publishing queue.

    Cancels the active queue item (preserving the audit trail) and
    flips the creative back to APPROVED so Creative Studio unlocks it.
    """
    try:
        rows = fetch_creatives_workflow(body.research_product_id)
        workflow = rows[0] if rows else None
        if workflow is None or workflow.get("creative_id") is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No creative exists for research product "
                    f"{body.research_product_id}."
                ),
            )

        ai_content_id = workflow.get("ai_content_id")

        if body.pin_id is not None:
            pin_id = body.pin_id
        else:
            active = fetch_active_queue_by_ai_content(ai_content_id)
            if not active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Creative for product {body.research_product_id} "
                        "is not in the publishing queue."
                    ),
                )
            pin_id = active[0]["pin_id"]

        mark_queue_cancelled(pin_id)
        unqueue_creative_from_publishing(body.research_product_id)
    except HTTPException:
        raise
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove creative from queue: {exc}",
        ) from exc

    logger.info(
        "Removed pin %s from publishing (product %s)",
        pin_id,
        body.research_product_id,
    )

    return PublishingActionResponse(
        success=True,
        pin_id=pin_id,
    )


@app.post(
    "/publishing/schedule",
    response_model=PublishingActionResponse,
)
def schedule_queued_pin_endpoint(
    body: PublishingScheduleRequest,
) -> PublishingActionResponse:
    """
    Schedule a queued pin by flipping it to READY with a publish time.
    """
    item = fetch_queue_item_details(body.pin_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No queue item {body.pin_id}.",
        )

    try:
        mark_queue_scheduled(body.pin_id, body.scheduled_at)
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule pin: {exc}",
        ) from exc

    content = fetch_queue_item_details(body.pin_id)

    logger.info(
        "Scheduled pin %s for %s",
        body.pin_id,
        body.scheduled_at,
    )

    return PublishingActionResponse(
        success=True,
        pin_id=body.pin_id,
        content=content,
    )


@app.post(
    "/publishing/publish-now",
    response_model=PublishingActionResponse,
)
def publish_queued_pin_now_endpoint(
    body: PublishingPublishNowRequest,
) -> PublishingActionResponse:
    """
    Publish a queued pin immediately through the Pinterest client.

    Reuses the same joined read model and ``publish_pin`` call as the
    publisher worker; on success the queue item is marked PUBLISHED.
    """
    item = fetch_queue_item_details(body.pin_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No queue item {body.pin_id}.",
        )

    if item.get("is_seed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Connect a Pinterest account before publishing. "
                "The destination account is a sample account used for "
                "local development."
            ),
        )

    try:
        success = publish_pin(
            title=item["pinterest_title"],
            description=item.get("pinterest_description") or "",
            image_url=item.get("image_url") or "",
            affiliate_url=item.get("affiliate_url") or "",
            board_name=item.get("board_name") or "Pinterest",
        )

        if success:
            mark_queue_published(body.pin_id)
            unqueue_creative_from_publishing(
                int(item["research_product_id"])
            )
        else:
            mark_queue_failed(
                body.pin_id,
                "Publishing returned False.",
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Publishing the pin failed.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        mark_queue_failed(body.pin_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Publishing failed: {exc}",
        ) from exc

    content = fetch_queue_item_details(body.pin_id)

    logger.info("Published pin %s", body.pin_id)

    return PublishingActionResponse(
        success=True,
        pin_id=body.pin_id,
        content=content,
    )


@app.post(
    "/publishing/board",
    response_model=PublishingActionResponse,
)
def update_queued_pin_board_endpoint(
    body: PublishingBoardRequest,
) -> PublishingActionResponse:
    """
    Change the destination account and board of a queued pin.
    """
    item = fetch_queue_item_details(body.pin_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No queue item {body.pin_id}.",
        )

    try:
        update_queue_board(
            body.pin_id,
            body.account_id,
            body.board_id,
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This creative is already tied to that account and board. "
                "Pick a different destination."
            ),
        ) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update pin board: {exc}",
        ) from exc

    content = fetch_queue_item_details(body.pin_id)

    logger.info(
        "Moved pin %s to account %s / board %s",
        body.pin_id,
        body.account_id,
        body.board_id,
    )

    return PublishingActionResponse(
        success=True,
        pin_id=body.pin_id,
        content=content,
    )


@app.get("/publishing/download/{creative_id}")
def download_creative_image(
    creative_id: int,
) -> FileResponse:
    """
    Stream a creative's stored PNG for download.

    Reads the path already persisted on ``creative_assets.image_path``
    rather than re-rendering the creative, so the downloaded pin exactly
    matches what is queued.
    """
    image_path = fetch_creative_image_path(creative_id)

    if not image_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No image stored for creative {creative_id}.",
        )

    path = Path(image_path)

    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creative image file not found: {path.name}",
        )

    return FileResponse(
        path,
        media_type="image/png",
    )


@app.post(
    "/creatives/reopen",
    response_model=CreativeActionResponse,
)
def reopen_creative_for_review_endpoint(
    body: CreativeReopenRequest,
) -> CreativeActionResponse:
    """
    Return an approved creative to the editable review state.

    Only the workflow status changes (APPROVED -> GENERATED); all
    editorial decisions (headline, CTA, template, variant, overlay,
    logo position, properties) are preserved. Queued creatives cannot
    be reopened — they must be removed from the publishing queue first.
    """
    try:
        creative_id = reopen_creative_for_review(body.research_product_id)
    except CreativeLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reopen creative: {exc}",
        ) from exc

    if creative_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No creative exists for research product "
                f"{body.research_product_id}."
            ),
        )

    rows = fetch_creatives_workflow(body.research_product_id)
    updated = rows[0] if rows else None

    logger.info(
        "Reopened creative %s for review (research product %s)",
        creative_id,
        body.research_product_id,
    )

    return CreativeActionResponse(
        success=True,
        creative_id=creative_id,
        content=updated,
    )
