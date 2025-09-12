from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import crud
import schemas
from dependencies import get_db

router = APIRouter(
    prefix="/admin/prompts",
    tags=["prompts"],
    # dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.Prompt)
def create_prompt(prompt: schemas.PromptCreate, db: Session = Depends(get_db)):
    return crud.create_prompt(db=db, prompt=prompt)


@router.get("/", response_model=List[schemas.Prompt])
def read_prompts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    prompts = crud.get_prompts(db, skip=skip, limit=limit)
    return prompts