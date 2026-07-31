"""
Atlas Core API — FastAPI application entry point.

Exposes health, categories, and jobs endpoints for Project Atlas.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from database import (
    claim_next_pending_job,
    create_job,
    fetch_all_categories,
    update_job_status,
)

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
        job_id = create_job(
            department=body.department,
            job_type=body.job_type,
            priority=body.priority,
            payload=body.payload,
        )
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
