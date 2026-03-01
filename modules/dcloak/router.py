from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.api_keys import require_scope
from modules.dcloak.core import obfuscate_data

router = APIRouter()


class FieldSpec(BaseModel):
    field: str
    strategy: str


class ObfuscateRequest(BaseModel):
    data: Dict[str, Any]
    fields: List[FieldSpec]


class ObfuscateResponse(BaseModel):
    data: Dict[str, Any]
    obfuscated_fields: List[str]
    skipped_fields: List[str]
    summary: str


@router.post("/obfuscate", response_model=ObfuscateResponse)
def obfuscate(
    req: ObfuscateRequest,
    _scopes: List[str] = Depends(require_scope("dcloak")),
):
    try:
        result = obfuscate_data(
            data=req.data,
            fields=[f.model_dump() for f in req.fields],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return result
