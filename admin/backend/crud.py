from sqlalchemy.orm import Session
import models
import schemas_legacy as schemas
from schemas import base_model
from schemas import system_config
from schemas import lora
from security import get_password_hash
import datetime

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
    return db.query(models.Workflow).order_by(models.Workflow.created_at.desc()).offset(skip).limit(limit).all()

def get_workflow(db: Session, workflow_id: int):
    return db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()

def create_workflow(db: Session, workflow: schemas.WorkflowCreate):
    db_workflow = models.Workflow(**workflow.dict())
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

def update_workflow(db: Session, workflow_id: int, workflow: schemas.WorkflowUpdate):
    db_workflow = db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()
    if db_workflow:
        update_data = workflow.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_workflow, key, value)
        db.commit()
        db.refresh(db_workflow)
    return db_workflow

def delete_workflow(db: Session, workflow_id: int):
    db_workflow = db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()
    if db_workflow:
        db.delete(db_workflow)
        db.commit()
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
        # 使用model_dump()替代dict()以兼容新版本Pydantic
        try:
            update_data = base_model.model_dump(exclude_unset=True)
        except AttributeError:
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

# 系统配置相关操作
def get_system_config(db: Session, key: str):
    return db.query(models.SystemConfig).filter(models.SystemConfig.key == key).first()

def get_system_configs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SystemConfig).offset(skip).limit(limit).all()

def create_system_config(db: Session, config: system_config.SystemConfigCreate):
    db_config = models.SystemConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def update_system_config(db: Session, key: str, config: system_config.SystemConfigUpdate):
    db_config = db.query(models.SystemConfig).filter(models.SystemConfig.key == key).first()
    if db_config:
        update_data = config.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_config, key, value)
        db.commit()
        db.refresh(db_config)
    return db_config

# LoRA相关操作
def get_lora(db: Session, lora_id: int):
    return db.query(models.Lora).filter(models.Lora.id == lora_id).first()

def get_lora_by_name(db: Session, name: str):
    return db.query(models.Lora).filter(models.Lora.name == name).first()

def get_loras(db: Session, skip: int = 0, limit: int = 100, base_model: str = None, name: str = None):
    query = db.query(models.Lora)
    if base_model:
        query = query.filter(models.Lora.base_model == base_model)
    if name:
        query = query.filter(models.Lora.name.contains(name))
    return query.offset(skip).limit(limit).all()

def create_lora(db: Session, lora_data: lora.LoraCreate):
    # 使用model_dump()替代dict()以兼容新版本Pydantic
    try:
        lora_dict = lora_data.model_dump()
    except AttributeError:
        lora_dict = lora_data.dict()
    db_lora = models.Lora(**lora_dict)
    db.add(db_lora)
    db.commit()
    db.refresh(db_lora)
    return db_lora

def update_lora(db: Session, lora_id: int, lora_data: lora.LoraUpdate):
    db_lora = db.query(models.Lora).filter(models.Lora.id == lora_id).first()
    if db_lora:
        # 使用model_dump()替代dict()以兼容新版本Pydantic
        try:
            update_data = lora_data.model_dump(exclude_unset=True)
        except AttributeError:
            update_data = lora_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_lora, key, value)
        # 手动设置updated_at
        db_lora.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(db_lora)
    return db_lora

def delete_lora(db: Session, lora_id: int):
    db_lora = db.query(models.Lora).filter(models.Lora.id == lora_id).first()
    if db_lora:
        db.delete(db_lora)
        db.commit()
    return db_lora