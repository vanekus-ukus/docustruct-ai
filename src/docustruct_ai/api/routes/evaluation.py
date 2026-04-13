from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from docustruct_ai.api.schemas import EvaluationRunRequest, EvaluationRunResponse
from docustruct_ai.db.session import get_db
from docustruct_ai.services.factory import get_evaluation_service

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/run", response_model=EvaluationRunResponse)
def run_evaluation(
    payload: EvaluationRunRequest,
    db: Session = Depends(get_db),
    evaluation_service=Depends(get_evaluation_service),
) -> EvaluationRunResponse:
    run = evaluation_service.run(
        db=db,
        name=payload.name,
        document_type=payload.document_type,
        items=[item.model_dump() for item in payload.items],
    )
    return EvaluationRunResponse(
        evaluation_run_id=run.id,
        status=run.status,
        summary=run.summary_json,
    )
