from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import os

import crud
import schemas_legacy as schemas
from dependencies import get_db
from workflow_validator import WorkflowValidator
from size_config_manager import SizeConfigManager

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


@router.get("/")
def read_workflows(skip: int = 0, limit: int = 100, search: str = "", db: Session = Depends(get_db)):
    workflows = crud.get_workflows(db, skip=skip, limit=limit, search=search)
    total = crud.get_workflows_count(db, search=search)
    
    return {
        "data": workflows,
        "total": total,
        "page": (skip // limit) + 1,
        "pageSize": limit,
        "hasMore": (skip + limit) < total
    }


@router.get("/size-mappings")
def get_size_mappings():
    """获取尺寸映射配置"""
    size_manager = SizeConfigManager()
    return {
        "ratios": [ratio.__dict__ for ratio in size_manager.get_available_ratios()],
        "statistics": size_manager.get_size_statistics()
    }

@router.get("/sizes/{ratio}")
def get_sizes_by_ratio(ratio: str):
    """根据比例获取可用尺寸"""
    size_manager = SizeConfigManager()
    sizes = size_manager.get_sizes_by_ratio(ratio)
    return {"sizes": [size.__dict__ for size in sizes]}

@router.get("/recommended-sizes")
def get_recommended_sizes(model_type: str = None, ratio: str = None):
    """获取推荐尺寸"""
    size_manager = SizeConfigManager()
    sizes = size_manager.get_recommended_sizes(model_type, ratio)
    return {"sizes": [size.__dict__ for size in sizes]}

@router.get("/default-size")
def get_default_size(model_type: str = None, ratio: str = "1:1"):
    """获取默认尺寸"""
    size_manager = SizeConfigManager()
    default_size = size_manager.get_default_size(model_type, ratio)
    return {"size": default_size.__dict__}

@router.get("/{workflow_id}", response_model=schemas.Workflow)
def read_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = crud.get_workflow(db, workflow_id=workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=schemas.Workflow)
def update_workflow(
    workflow_id: int, 
    workflow: schemas.WorkflowUpdate, 
    db: Session = Depends(get_db)
):
    db_workflow = crud.update_workflow(db, workflow_id=workflow_id, workflow=workflow)
    if db_workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return db_workflow


@router.patch("/{workflow_id}/status")
def update_workflow_status(
    workflow_id: int, 
    status_data: Dict[str, str], 
    db: Session = Depends(get_db)
):
    """更新工作流状态（启用/禁用）"""
    workflow = crud.get_workflow(db, workflow_id=workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="工作流未找到")
    
    new_status = status_data.get("status")
    if new_status not in ["enabled", "disabled"]:
        raise HTTPException(status_code=400, detail="状态值必须是 'enabled' 或 'disabled'")
    
    return crud.update_workflow_status(db=db, workflow_id=workflow_id, status=new_status)

@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """删除工作流（只能删除禁用的工作流）"""
    workflow = crud.get_workflow(db, workflow_id=workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="工作流未找到")
    
    if workflow.status == "enabled":
        raise HTTPException(status_code=400, detail="只能删除禁用的工作流，请先禁用工作流")
    
    return crud.delete_workflow(db=db, workflow_id=workflow_id)


@router.post("/upload", response_model=schemas.Workflow)
def upload_workflow_file(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    db: Session = Depends(get_db)
):
    """上传工作流JSON文件"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")
    
    try:
        # 读取文件内容
        content = file.file.read().decode('utf-8')
        workflow_json = json.loads(content)
        
        # 使用文件名作为名称（如果没有提供名称）
        workflow_name = name or file.filename.replace('.json', '')
        
        # 创建工作流
        workflow_data = schemas.WorkflowCreate(
            name=workflow_name,
            description=description,
            workflow_json=workflow_json
        )
        
        return crud.create_workflow(db=db, workflow=workflow_data)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/{workflow_id}/download")
def download_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """下载工作流JSON文件"""
    workflow = crud.get_workflow(db, workflow_id=workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 返回JSON内容
    return {
        "filename": f"{workflow.name}.json",
        "content": workflow.workflow_json,
        "name": workflow.name,
        "description": workflow.description
    }

@router.post("/validate")
def validate_workflow(workflow_data: Dict[str, Any]):
    """验证工作流JSON并分析配置项"""
    try:
        # 提取工作流JSON数据
        workflow_json = workflow_data.get("workflow_json", workflow_data)
        
        validator = WorkflowValidator()
        result = validator.validate_and_analyze_workflow(workflow_json)
        
        return {
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "node_analysis": result.node_analysis,
            "config_items": result.config_items,
            "config_template": result.config_template
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")

@router.post("/upload-and-validate")
def upload_and_validate_workflow(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    db: Session = Depends(get_db)
):
    """上传工作流文件并验证"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")
    
    try:
        # 读取文件内容
        content = file.file.read().decode('utf-8')
        workflow_json = json.loads(content)
        
        # 验证工作流
        validator = WorkflowValidator()
        validation_result = validator.validate_and_analyze_workflow(workflow_json)
        
        if not validation_result.valid:
            return {
                "valid": False,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings
            }
        
        # 如果提供了名称和描述，创建工作流记录
        if name and description:
            workflow_data = schemas.WorkflowCreate(
                name=name,
                description=description,
                workflow_json=workflow_json
            )
            workflow = crud.create_workflow(db=db, workflow=workflow_data)
            
            return {
                "valid": True,
                "workflow_id": workflow.id,
                "node_analysis": validation_result.node_analysis,
                "config_items": validation_result.config_items,
                "config_template": validation_result.config_template,
                "warnings": validation_result.warnings
            }
        else:
            return {
                "valid": True,
                "node_analysis": validation_result.node_analysis,
                "config_items": validation_result.config_items,
                "config_template": validation_result.config_template,
                "warnings": validation_result.warnings
            }
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/create-from-upload")
def create_workflow_from_upload(
    workflow_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """从上传的工作流创建配置"""
    try:
        # 验证工作流
        validator = WorkflowValidator()
        validation_result = validator.validate_and_analyze_workflow(workflow_config["workflow_json"])
        
        if not validation_result.valid:
            raise HTTPException(status_code=400, detail="工作流验证失败")
        
        # 创建工作流记录
        workflow_data = schemas.WorkflowCreate(
            name=workflow_config["name"],
            description=workflow_config["description"],
            workflow_json=workflow_config["workflow_json"]
        )
        workflow = crud.create_workflow(db=db, workflow=workflow_data)
        
        return {
            "workflow_id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "config_template": validation_result.config_template,
            "node_analysis": validation_result.node_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工作流失败: {str(e)}")

@router.post("/validate-size")
def validate_size(size_data: Dict[str, Any]):
    """验证尺寸"""
    width = size_data.get("width")
    height = size_data.get("height")
    model_type = size_data.get("model_type")
    
    if not width or not height:
        raise HTTPException(status_code=400, detail="Width and height are required")
    
    size_manager = SizeConfigManager()
    is_valid, message = size_manager.validate_size(width, height, model_type)
    
    return {
        "valid": is_valid,
        "message": message,
        "size_info": size_manager.get_size_info(width, height).__dict__ if is_valid else None
    }