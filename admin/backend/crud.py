from sqlalchemy.orm import Session
import models
import schemas_legacy as schemas
from schemas import base_model
from security import get_password_hash

def get_user_by_username(db: Session, username: str):
    return db.query(models.AdminUser).filter(models.AdminUser.username == username).first()

def create_user(db: Session, user: schemas.AdminUserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.AdminUser(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_inspiration(db: Session, inspiration_id: int):
    return db.query(models.Inspiration).filter(models.Inspiration.id == inspiration_id).first()

def get_inspirations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Inspiration).offset(skip).limit(limit).all()

def create_inspiration(db: Session, inspiration: schemas.InspirationCreate):
    db_inspiration = models.Inspiration(**inspiration.dict())
    db.add(db_inspiration)
    db.commit()
    db.refresh(db_inspiration)
    return db_inspiration

def update_inspiration(db: Session, inspiration_id: int, inspiration: schemas.InspirationUpdate):
    db_inspiration = get_inspiration(db, inspiration_id)
    if db_inspiration:
        update_data = inspiration.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_inspiration, key, value)
        db.commit()
        db.refresh(db_inspiration)
    return db_inspiration

def delete_inspiration(db: Session, inspiration_id: int):
    db_inspiration = get_inspiration(db, inspiration_id)
    if db_inspiration:
        db.delete(db_inspiration)
        db.commit()
    return db_inspiration

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AdminAuditLog).order_by(models.AdminAuditLog.timestamp.desc()).offset(skip).limit(limit).all()

def get_workflows(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Workflow).offset(skip).limit(limit).all()

def create_workflow(db: Session, workflow: schemas.WorkflowCreate):
    db_workflow = models.Workflow(**workflow.dict())
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

def get_prompts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Prompt).offset(skip).limit(limit).all()

def create_prompt(db: Session, prompt: schemas.PromptCreate):
    db_prompt = models.Prompt(**prompt.dict())
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

def create_base_model(db: Session, base_model: base_model.BaseModelCreate):
    db_base_model = models.BaseModel(**base_model.dict())
    db.add(db_base_model)
    db.commit()
    db.refresh(db_base_model)
    return db_base_model

def get_base_model(db: Session, base_model_id: int):
    return db.query(models.BaseModel).filter(models.BaseModel.id == base_model_id).first()

def get_base_models(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.BaseModel).offset(skip).limit(limit).all()

def update_base_model(db: Session, base_model_id: int, base_model: base_model.BaseModelUpdate):
    db_base_model = db.query(models.BaseModel).filter(models.BaseModel.id == base_model_id).first()
    if db_base_model:
        update_data = base_model.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_base_model, key, value)
        db.commit()
        db.refresh(db_base_model)
    return db_base_model

def delete_base_model(db: Session, base_model_id: int):
    db_base_model = db.query(models.BaseModel).filter(models.BaseModel.id == base_model_id).first()
    if db_base_model:
        db.delete(db_base_model)
        db.commit()
    return db_base_model