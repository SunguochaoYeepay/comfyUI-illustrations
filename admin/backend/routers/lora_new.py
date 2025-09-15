from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import models
from schemas import lora
from dependencies import get_db, get_current_user
from config import settings

router = APIRouter()

@router.get("/loras/", response_model=dict)
async def get_loras(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    base_model: Optional[str] = Query(None, description="基础模型过滤"),
    name: Optional[str] = Query(None, description="名称搜索"),
    db: Session = Depends(get_db),
    # current_user: models.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """获取LoRA列表"""
    try:
        skip = (page - 1) * page_size
        loras = crud.get_loras(db, skip=skip, limit=page_size, base_model=base_model, name=name)
        
        # 获取总数
        total_query = db.query(models.Lora)
        if base_model:
            total_query = total_query.filter(models.Lora.base_model == base_model)
        if name:
            total_query = total_query.filter(models.Lora.name.contains(name))
        total = total_query.count()
        
        # 将SQLAlchemy对象转换为字典
        loras_data = []
        for lora in loras:
            lora_dict = {
                "id": lora.id,
                "name": lora.name,
                "display_name": lora.display_name,
                "base_model": lora.base_model,
                "description": lora.description,
                "file_path": lora.file_path,
                "file_size": lora.file_size,
                "is_available": lora.is_available,
                "is_managed": lora.is_managed,
                "created_at": lora.created_at.isoformat() if lora.created_at else None,
                "updated_at": lora.updated_at.isoformat() if lora.updated_at else None
            }
            loras_data.append(lora_dict)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "items": loras_data,
                "total": total,
                "page": page,
                "pageSize": page_size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取LoRA列表失败: {str(e)}")

@router.get("/loras/{lora_id}", response_model=dict)
async def get_lora(
    lora_id: int,
    db: Session = Depends(get_db),
    # current_user: models.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """获取单个LoRA详情"""
    try:
        lora_data = crud.get_lora(db, lora_id)
        if not lora_data:
            raise HTTPException(status_code=404, detail="LoRA不存在")
        
        # 手动序列化数据
        lora_dict = {
            "id": lora_data.id,
            "name": lora_data.name,
            "display_name": lora_data.display_name,
            "base_model": lora_data.base_model,
            "description": lora_data.description,
            "file_path": lora_data.file_path,
            "file_size": lora_data.file_size,
            "is_available": lora_data.is_available,
            "is_managed": lora_data.is_managed,
            "created_at": lora_data.created_at.isoformat() if lora_data.created_at else None,
            "updated_at": lora_data.updated_at.isoformat() if lora_data.updated_at else None
        }
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": lora_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取LoRA详情失败: {str(e)}")

@router.put("/loras/{lora_id}", response_model=dict)
async def update_lora(
    lora_id: int,
    lora_data: lora.LoraUpdate,
    db: Session = Depends(get_db),
    # current_user: models.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """更新LoRA信息"""
    try:
        updated_lora = crud.update_lora(db, lora_id, lora_data)
        if not updated_lora:
            raise HTTPException(status_code=404, detail="LoRA不存在")
        
        # 手动序列化数据
        lora_dict = {
            "id": updated_lora.id,
            "name": updated_lora.name,
            "display_name": updated_lora.display_name,
            "base_model": updated_lora.base_model,
            "description": updated_lora.description,
            "file_path": updated_lora.file_path,
            "file_size": updated_lora.file_size,
            "is_available": updated_lora.is_available,
            "is_managed": updated_lora.is_managed,
            "created_at": updated_lora.created_at.isoformat() if updated_lora.created_at else None,
            "updated_at": updated_lora.updated_at.isoformat() if updated_lora.updated_at else None
        }
        
        return {
            "code": 200,
            "message": "更新成功",
            "data": lora_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新LoRA失败: {str(e)}")

@router.delete("/loras/{lora_id}", response_model=dict)
async def delete_lora(
    lora_id: int,
    db: Session = Depends(get_db),
    # current_user: models.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """删除LoRA"""
    try:
        deleted_lora = crud.delete_lora(db, lora_id)
        if not deleted_lora:
            raise HTTPException(status_code=404, detail="LoRA不存在")
        
        return {
            "code": 200,
            "message": "删除成功",
            "data": {"id": lora_id}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除LoRA失败: {str(e)}")

@router.post("/loras/", response_model=dict)
async def create_lora(
    lora_data: lora.LoraCreate,
    db: Session = Depends(get_db),
    # current_user: models.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """创建LoRA记录"""
    try:
        # 检查名称是否已存在
        existing_lora = crud.get_lora_by_name(db, lora_data.name)
        if existing_lora:
            raise HTTPException(status_code=400, detail="LoRA名称已存在")
        
        new_lora = crud.create_lora(db, lora_data)
        
        return {
            "code": 200,
            "message": "创建成功",
            "data": new_lora
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建LoRA失败: {str(e)}")

@router.get("/loras/unassociated/list", response_model=dict)
async def get_unassociated_loras(
    db: Session = Depends(get_db),
    # current_user: models.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """获取未关联的LoRA文件列表"""
    try:
        from pathlib import Path
        import os
        
        # 获取LoRA目录路径
        loras_dir = Path(settings.COMFYUI_LORAS_DIR)
        
        if not loras_dir.exists():
            return {
                "code": 200,
                "message": "获取成功",
                "data": []
            }
        
        # 扫描LoRA目录中的所有.safetensors文件
        lora_files = []
        for file_path in loras_dir.glob("*.safetensors"):
            if file_path.is_file():
                lora_files.append(file_path.name)
        
        # 获取数据库中已存在的LoRA文件名
        existing_loras = crud.get_loras(db, skip=0, limit=1000)  # 获取所有LoRA记录
        existing_names = {lora.name for lora in existing_loras}
        
        # 找出未关联的文件，如果没有未关联的文件，则返回所有文件供选择
        unassociated_files = [name for name in lora_files if name not in existing_names]
        if not unassociated_files:
            # 如果没有未关联的文件，返回所有文件供用户选择
            unassociated_files = lora_files
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": unassociated_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取未关联LoRA失败: {str(e)}")
