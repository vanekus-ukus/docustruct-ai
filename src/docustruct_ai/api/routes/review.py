from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from docustruct_ai.api.schemas import ReviewSubmitRequest, ReviewSubmitResponse
from docustruct_ai.db.session import get_db
from docustruct_ai.services.factory import get_review_service

router = APIRouter(prefix="/review", tags=["review"])


@router.post("/tasks/{task_id}/submit", response_model=ReviewSubmitResponse)
def submit_review_task(
    task_id: int,
    payload: ReviewSubmitRequest,
    db: Session = Depends(get_db),
    review_service=Depends(get_review_service),
) -> ReviewSubmitResponse:
    if payload.decision not in {"accept", "edit", "unsupported"}:
        raise HTTPException(status_code=400, detail="Unsupported decision")
    task = review_service.submit(
        db=db,
        task_id=task_id,
        decision=payload.decision,
        final_value=payload.final_value,
        reviewer=payload.reviewer,
        comment=payload.comment,
    )
    return ReviewSubmitResponse(review_task_id=task.id, status=task.status, decision=payload.decision)
