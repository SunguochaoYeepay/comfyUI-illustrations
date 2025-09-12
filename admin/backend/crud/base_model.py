from sqlalchemy.orm import Session
from models import BaseModel
from schemas import BaseModelCreate, BaseModelUpdate

def get_base_model(db: Session, base_model_id: int):
    return db.query(BaseModel).filter(BaseModel.id == base_model_id).first()

def get_base_models(db: Session, skip: int = 0, limit: int = 100):
    return db.query(BaseModel).offset(skip).limit(limit).all()

def create_base_model(db: Session, base_model: BaseModelCreate):
    db_base_model = BaseModel(**base_model.dict())
    db.add(db_base_model)
    db.commit()
    db.refresh(db_base_model)
    return db_base_model

def update_base_model(db: Session, base_model_id: int, base_model: BaseModelUpdate):
    db_base_model = get_base_model(db, base_model_id)
    if db_base_model:
        update_data = base_model.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_base_model, key, value)
        db.commit()
        db.refresh(db_base_model)
    return db_base_model

def delete_base_model(db: Session, base_model_id: int):
    db_base_model = get_base_model(db, base_model_id)
    if db_base_model:
        db.delete(db_base_model)
        db.commit()
    return db_base_model