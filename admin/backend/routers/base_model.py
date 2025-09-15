from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from dependencies import get_db
import crud
import models
from schemas import base_model

router = APIRouter()

@router.post("/base_models/", response_model=base_model.BaseModel, summary="创建基础模型")
def create_base_model(model_create: base_model.BaseModelCreate, db: Session = Depends(get_db)):
    return crud.create_base_model(db=db, base_model=model_create)

@router.get("/base_models/{base_model_id}", response_model=base_model.BaseModel, summary="获取单个基础模型")
def read_base_model(base_model_id: int, db: Session = Depends(get_db)):
    db_base_model = crud.get_base_model(db, base_model_id=base_model_id)
    if db_base_model is None:
        raise HTTPException(status_code=404, detail="Base model not found")
    return db_base_model

@router.get("/base_models/", summary="获取基础模型列表")
def read_base_models(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    skip = (page - 1) * size
    base_models = crud.get_base_models(db, skip=skip, limit=size)
    total = db.query(models.BaseModel).count()
    # 将SQLAlchemy对象转换为字典
    base_models_data = []
    for model in base_models:
        model_dict = {
            "id": model.id,
            "name": model.name,
            "display_name": model.display_name,
            "model_type": model.model_type,
            "description": model.description,
            "unet_file": model.unet_file,
            "clip_file": model.clip_file,
            "vae_file": model.vae_file,
            "template_path": model.template_path,
            "preview_image_path": model.preview_image_path,
            "is_available": model.is_available,
            "is_default": model.is_default,
            "sort_order": model.sort_order,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        }
        base_models_data.append(model_dict)
    
    return {
        "code": 200,
        "message": "Success",
        "data": {
            "items": base_models_data,
            "total": total,
            "page": page,
            "size": size
        }
    }

@router.put("/base_models/{base_model_id}", response_model=base_model.BaseModel, summary="更新基础模型")
def update_base_model(base_model_id: int, model_update: base_model.BaseModelUpdate, db: Session = Depends(get_db)):
    db_base_model = crud.update_base_model(db, base_model_id=base_model_id, base_model=model_update)
    if db_base_model is None:
        raise HTTPException(status_code=404, detail="Base model not found")
    return db_base_model

@router.delete("/base_models/{base_model_id}", response_model=base_model.BaseModel, summary="删除基础模型")
def delete_base_model(base_model_id: int, db: Session = Depends(get_db)):
    db_base_model = crud.delete_base_model(db, base_model_id=base_model_id)
    if db_base_model is None:
        raise HTTPException(status_code=404, detail="Base model not found")
    return db_base_model