import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json

import crud
import schemas_legacy as schemas
from dependencies import get_db
from workflow_validator import WorkflowValidator

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
def read_workflows(
    skip: int = 0, 
    limit: int = 100, 
    search: str = "", 
    base_model_type: Optional[str] = Query(None, description="按基础模型类型过滤"),
    db: Session = Depends(get_db)
):
    workflows = crud.get_workflows(db, skip=skip, limit=limit, search=search, base_model_type=base_model_type)
    total = crud.get_workflows_count(db, search=search, base_model_type=base_model_type)
    
    return {
        "data": workflows,
        "total": total,
        "page": (skip // limit) + 1,
        "pageSize": limit,
        "hasMore": (skip + limit) < total
    }



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
