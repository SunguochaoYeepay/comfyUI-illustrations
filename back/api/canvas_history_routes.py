#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画布历史记录API路由
提供画布历史记录的CRUD操作
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from models.schemas import (
    CanvasHistoryCreateRequest,
    CanvasHistoryUpdateRequest,
    CanvasHistoryBatchCreateRequest,
    CanvasHistoryResponse,
    CanvasHistoryListResponse,
    CanvasHistoryDeleteResponse
)
from core.service_manager import get_db_manager

# 创建路由器
router = APIRouter(prefix="/api/canvas", tags=["canvas-history"])

# 获取数据库管理器
db_manager = get_db_manager()


@router.post("/history", response_model=CanvasHistoryResponse)
async def create_history_record(record: CanvasHistoryCreateRequest):
    """创建画布历史记录"""
    try:
        # 准备数据
        record_data = {
            'id': record.id,
            'task_id': record.task_id,
            'prompt': record.prompt,
            'original_image_url': record.original_image_url,
            'result_image_url': record.result_image_url,
            'parameters': record.parameters,
            'timestamp': record.timestamp,
            'type': record.type
        }
        
        # 保存到数据库
        db_manager.create_canvas_history_record(record_data)
        
        # 返回创建的记录
        created_record = db_manager.get_canvas_history_record(record.id)
        if not created_record:
            raise HTTPException(status_code=500, detail="Failed to retrieve created record")
        
        return CanvasHistoryResponse(**created_record)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create history record: {str(e)}")


@router.get("/history", response_model=CanvasHistoryListResponse)
async def get_history_records(
    limit: int = Query(50, ge=1, le=100, description="每页记录数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    order: str = Query("desc", regex="^(asc|desc)$", description="排序方式")
):
    """获取画布历史记录列表"""
    try:
        result = db_manager.get_canvas_history_records(limit=limit, offset=offset, order=order)
        
        # 转换为响应格式
        records = [CanvasHistoryResponse(**record) for record in result['records']]
        
        return CanvasHistoryListResponse(
            records=records,
            total=result['total'],
            limit=result['limit'],
            offset=result['offset']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history records: {str(e)}")


@router.get("/history/{record_id}", response_model=CanvasHistoryResponse)
async def get_history_record(record_id: str):
    """获取单个画布历史记录"""
    try:
        record = db_manager.get_canvas_history_record(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="History record not found")
        
        return CanvasHistoryResponse(**record)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history record: {str(e)}")


@router.put("/history/{record_id}", response_model=CanvasHistoryResponse)
async def update_history_record(record_id: str, updates: CanvasHistoryUpdateRequest):
    """更新画布历史记录"""
    try:
        # 检查记录是否存在
        existing_record = db_manager.get_canvas_history_record(record_id)
        if not existing_record:
            raise HTTPException(status_code=404, detail="History record not found")
        
        # 准备更新数据
        update_data = {}
        if updates.prompt is not None:
            update_data['prompt'] = updates.prompt
        if updates.parameters is not None:
            update_data['parameters'] = updates.parameters
        
        # 执行更新
        success = db_manager.update_canvas_history_record(record_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update history record")
        
        # 返回更新后的记录
        updated_record = db_manager.get_canvas_history_record(record_id)
        return CanvasHistoryResponse(**updated_record)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update history record: {str(e)}")


@router.delete("/history/{record_id}", response_model=CanvasHistoryDeleteResponse)
async def delete_history_record(record_id: str):
    """删除画布历史记录"""
    try:
        # 检查记录是否存在
        existing_record = db_manager.get_canvas_history_record(record_id)
        if not existing_record:
            raise HTTPException(status_code=404, detail="History record not found")
        
        # 执行删除
        success = db_manager.delete_canvas_history_record(record_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete history record")
        
        return CanvasHistoryDeleteResponse(
            id=record_id,
            message="History record deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete history record: {str(e)}")


@router.post("/history/batch", response_model=dict)
async def batch_create_history_records(batch_request: CanvasHistoryBatchCreateRequest):
    """批量创建画布历史记录"""
    try:
        # 准备数据
        records_data = []
        for record in batch_request.records:
            record_data = {
                'id': record.id,
                'task_id': record.task_id,
                'prompt': record.prompt,
                'original_image_url': record.original_image_url,
                'result_image_url': record.result_image_url,
                'parameters': record.parameters,
                'timestamp': record.timestamp,
                'type': record.type
            }
            records_data.append(record_data)
        
        # 批量保存
        success_count = db_manager.batch_create_canvas_history_records(records_data)
        
        return {
            "message": f"Successfully created {success_count} out of {len(records_data)} records",
            "success_count": success_count,
            "total_count": len(records_data),
            "failed_count": len(records_data) - success_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch create history records: {str(e)}")


@router.delete("/history", response_model=dict)
async def clear_all_history_records():
    """清空所有画布历史记录"""
    try:
        # 获取所有记录
        all_records = db_manager.get_canvas_history_records(limit=10000, offset=0)
        
        # 删除所有记录
        deleted_count = 0
        for record in all_records['records']:
            if db_manager.delete_canvas_history_record(record['id']):
                deleted_count += 1
        
        return {
            "message": f"Successfully deleted {deleted_count} history records",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear history records: {str(e)}")
