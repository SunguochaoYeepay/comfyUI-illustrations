from fastapi import APIRouter, Depends, HTTPException
from typing import List
import httpx

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)

async def fetch_tasks_from_main_backend():
    """
    从主后端获取所有任务数据。
    """
    try:
        async with httpx.AsyncClient() as client:
            # 注意：这里我们直接调用主后端的 /api/history 接口
            response = await client.get(f"{settings.BACKEND_URL}/api/history")
            response.raise_for_status()
            return response.json().get("tasks", [])
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        print(f"Error fetching tasks from main backend: {e}")
        return []

@router.get("/queue")
async def get_task_queue():
    """
    获取当前任务队列（运行中和待处理）。
    """
    all_tasks = await fetch_tasks_from_main_backend()
    queue_tasks = [task for task in all_tasks if task.get("status") in ["running", "pending"]]
    return queue_tasks

@router.get("/history")
async def get_task_history():
    """
    获取已完成或失败的任务历史。
    """
    all_tasks = await fetch_tasks_from_main_backend()
    history_tasks = [task for task in all_tasks if task.get("status") in ["completed", "failed"]]
    return history_tasks

@router.get("/{task_id}")
async def get_task_details(task_id: str):
    """
    获取特定任务的详细信息。
    """
    all_tasks = await fetch_tasks_from_main_backend()
    for task in all_tasks:
        if task.get("task_id") == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")