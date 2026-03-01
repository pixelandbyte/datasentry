from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.api_keys import require_scope
from modules.dv.core import validate_data

router = APIRouter()


class ValidationRule(BaseModel):
    field: str
    type: str
    required: Optional[bool] = False
    allowed_values: Optional[List[Any]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None


class ValidateRequest(BaseModel):
    data: Dict[str, Any]
    rules: List[ValidationRule]


class ValidationError(BaseModel):
    field: str
    issue: str
    value_received: str


class ValidateResponse(BaseModel):
    valid: bool
    errors: List[ValidationError]
    summary: str


@router.post("/validate", response_model=ValidateResponse)
def validate(
    req: ValidateRequest,
    _scopes: List[str] = Depends(require_scope("dv")),
):
    if len(req.rules) == 0:
        raise HTTPException(status_code=400, detail="rules must not be empty")

    try:
        result = validate_data(
            data=req.data,
            rules=[r.model_dump() for r in req.rules],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return result
