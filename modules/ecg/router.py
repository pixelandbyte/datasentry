from typing import List, Literal, Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.api_keys import require_scope
from modules.ecg.core import analyze_pipeline

router = APIRouter()


class AnalyzeRequest(BaseModel):
    pipeline_description: str
    platform: Literal["zapier", "make", "n8n"]
    context: Optional[str] = None


class AnalyzeResponse(BaseModel):
    edge_cases: List[str]
    failure_scenarios: List[str]
    assumptions_flagged: List[str]
    summary: str


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    req: AnalyzeRequest,
    _scopes: List[str] = Depends(require_scope("ecg")),
):
    if not req.pipeline_description.strip():
        raise HTTPException(status_code=400, detail="pipeline_description must not be empty")
    if len(req.pipeline_description) > 5000:
        raise HTTPException(status_code=400, detail="pipeline_description must be 5000 characters or fewer")

    try:
        result = analyze_pipeline(
            pipeline_description=req.pipeline_description,
            platform=req.platform,
            context=req.context,
        )
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {e}") from e
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return result
