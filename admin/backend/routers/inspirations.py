from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import crud
import models
import schemas_legacy as schemas
from dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/inspirations",
    tags=["inspirations"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.Inspiration)
def create_inspiration(inspiration: schemas.InspirationCreate, db: Session = Depends(get_db)):
    return crud.create_inspiration(db=db, inspiration=inspiration)

@router.get("/", response_model=List[schemas.Inspiration])
def read_inspirations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    inspirations = crud.get_inspirations(db, skip=skip, limit=limit)
    return inspirations

@router.get("/{inspiration_id}", response_model=schemas.Inspiration)
def read_inspiration(inspiration_id: int, db: Session = Depends(get_db)):
    db_inspiration = crud.get_inspiration(db, inspiration_id=inspiration_id)
    if db_inspiration is None:
        raise HTTPException(status_code=404, detail="Inspiration not found")
    return db_inspiration

@router.put("/{inspiration_id}", response_model=schemas.Inspiration)
def update_inspiration(inspiration_id: int, inspiration: schemas.InspirationUpdate, db: Session = Depends(get_db)):
    db_inspiration = crud.get_inspiration(db, inspiration_id=inspiration_id)
    if db_inspiration is None:
        raise HTTPException(status_code=404, detail="Inspiration not found")
    return crud.update_inspiration(db=db, inspiration_id=inspiration_id, inspiration=inspiration)

@router.delete("/{inspiration_id}", response_model=schemas.Inspiration)
def delete_inspiration(inspiration_id: int, db: Session = Depends(get_db)):
    db_inspiration = crud.get_inspiration(db, inspiration_id=inspiration_id)
    if db_inspiration is None:
        raise HTTPException(status_code=404, detail="Inspiration not found")
    return crud.delete_inspiration(db=db, inspiration_id=inspiration_id)