from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud
import schemas_legacy as schemas
from dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    # This is a placeholder. In a real application, you would fetch
    # stats from the database and other services.
    return {
        "system_status": {
            "fastapi_backend": "running",
            "comfyui_connection": "connected"
        },
        "task_queue": {
            "pending": 0,
            "running": 0,
            "average_completion_time": 0
        },
        "core_stats": {
            "images_generated": 0,
            "tasks_processed": 0,
            "storage_usage": 0
        }
    }