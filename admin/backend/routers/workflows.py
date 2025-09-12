from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import crud
import schemas
from dependencies import get_db

router = APIRouter(
    prefix="/admin/workflows",
    tags=["workflows"],
    # dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.Workflow)
def create_workflow(
    workflow: schemas.WorkflowCreate, db: Session = Depends(get_db)
):
    return crud.create_workflow(db=db, workflow=workflow)


@router.get("/", response_model=List[schemas.Workflow])
def read_workflows(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    workflows = crud.get_workflows(db, skip=skip, limit=limit)
    return workflows