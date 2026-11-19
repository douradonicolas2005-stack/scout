from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas.collection import (
    CollectionJobCreate,
    CollectionJobListResponse,
    CollectionJobResponse,
    CollectionRunListResponse,
    CollectionRunResponse,
    JobExecutionResponse,
    ProcessingEventListResponse,
    ProcessingEventResponse,
)
from app.db.session import get_db
from app.ingestion.collection import (
    CollectionError,
    create_collection_job,
    execute_collection_job,
    get_job_runs,
    get_run_events,
)
from app.knowledge.models.domain import CollectionJob, CollectionRun

router = APIRouter()


@router.post(
    "/ingestion/jobs",
    response_model=JobExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    payload: CollectionJobCreate, db: Session = Depends(get_db)
) -> JobExecutionResponse:
    try:
        job = create_collection_job(
            db,
            source_id=payload.source_id,
            trigger=payload.trigger,
            requested_by=payload.requested_by,
            scheduled_for=payload.scheduled_for,
            max_attempts=payload.max_attempts,
        )
        run = None
        if payload.execute_now:
            run = execute_collection_job(db, job.id)
            db.refresh(job)
        return JobExecutionResponse(
            job=CollectionJobResponse.model_validate(job),
            run=CollectionRunResponse.model_validate(run) if run else None,
        )
    except CollectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get("/ingestion/jobs", response_model=CollectionJobListResponse)
def list_jobs(
    source_id: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> CollectionJobListResponse:
    stmt = select(CollectionJob).order_by(CollectionJob.created_at.desc())
    if source_id:
        stmt = stmt.where(CollectionJob.source_id == source_id)
    if status_filter:
        stmt = stmt.where(CollectionJob.status == status_filter)
    rows = db.execute(stmt).scalars().all()
    return CollectionJobListResponse(
        items=[CollectionJobResponse.model_validate(r) for r in rows]
    )


@router.get("/ingestion/jobs/{job_id}", response_model=CollectionJobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)) -> CollectionJobResponse:
    job = db.get(CollectionJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return CollectionJobResponse.model_validate(job)


@router.post("/ingestion/jobs/{job_id}/run", response_model=JobExecutionResponse)
def run_job(job_id: str, db: Session = Depends(get_db)) -> JobExecutionResponse:
    job = db.get(CollectionJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    try:
        run = execute_collection_job(db, job_id)
        db.refresh(job)
        return JobExecutionResponse(
            job=CollectionJobResponse.model_validate(job),
            run=CollectionRunResponse.model_validate(run),
        )
    except CollectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get("/ingestion/jobs/{job_id}/runs", response_model=CollectionRunListResponse)
def list_job_runs(job_id: str, db: Session = Depends(get_db)) -> CollectionRunListResponse:
    job = db.get(CollectionJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    rows = get_job_runs(db, job_id)
    return CollectionRunListResponse(
        items=[CollectionRunResponse.model_validate(r) for r in rows]
    )


@router.get("/ingestion/runs/{run_id}", response_model=CollectionRunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)) -> CollectionRunResponse:
    run = db.get(CollectionRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return CollectionRunResponse.model_validate(run)


@router.get("/ingestion/runs/{run_id}/events", response_model=ProcessingEventListResponse)
def list_run_events(
    run_id: str, db: Session = Depends(get_db)
) -> ProcessingEventListResponse:
    run = db.get(CollectionRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    rows = get_run_events(db, run_id)
    return ProcessingEventListResponse(
        items=[ProcessingEventResponse.model_validate(r) for r in rows]
    )
