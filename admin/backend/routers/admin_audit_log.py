from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

import crud, schemas
from dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit-logs"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.AdminAuditLog])
def read_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logs = crud.get_audit_logs(db, skip=skip, limit=limit)
    return logs