from fastapi import APIRouter, Depends
from typing import List
import httpx
import json

# This is a placeholder for where you might get your image data from.
# In a real application, this would be from a database or a file system.
# fake_image_db = [
#     {"image_id": "img001", "url": "/static/img001.png", "prompt": "a cat sitting on a table"},
#     {"image_id": "img002", "url": "/static/img002.png", "prompt": "a dog playing in the park"}
# ]

router = APIRouter(
    prefix="/images",
    tags=["images"],
    # dependencies=[Depends(get_current_user)], # Add security back later
    responses={404: {"description": "Not found"}},
)

@router.get("/")
@router.get("/list_images")
async def list_images():
    formatted_images = []
    try:
        async with httpx.AsyncClient() as client:
            # 使用配置中的后端URL
            response = await client.get(f"{settings.BACKEND_URL}/api/history")
            response.raise_for_status()  # Raise an exception for bad status codes
            history_data = response.json()

            # The main backend returns a 'tasks' list, not a 'history' dict.
            if "tasks" in history_data:
                for task_info in history_data["tasks"]:
                    task_id = task_info.get("id")
                    if not task_id:
                        continue

                    # The structure for outputs might be nested inside the task object.
                    # This part of the logic assumes 'outputs' exists and has the expected structure.
                    if "outputs" in task_info:
                        for output in task_info["outputs"]:
                            if output.get('type') == 'image_generated' and 'image_urls' in output:
                                for img_info in output['image_urls']:
                                    formatted_images.append({
                                        "image_id": f"{task_id}_{img_info.get('filename', '')}",
                                        # 使用配置中的后端URL
                                        "url": f"{settings.BACKEND_URL}/api/image/{task_id}/{img_info.get('index', '')}",
                                        "prompt": task_info.get("description", ""), # Use 'description' as prompt
                                        "status": task_info.get("status", "unknown"),
                                        "create_time": task_info.get("timestamp", ""),
                                    })
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}: {e!r}")
        # Return empty list if the main backend is not available
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e!r}")
        # Return empty list for any other unexpected errors
        return []

    return formatted_images

@router.get("/{image_id}")
async def get_image_details(image_id: str):
    """
    Get details for a specific image.
    """
    for image in fake_image_db:
        if image["image_id"] == image_id:
            return image
    return {"error": "Image not found"}

@router.delete("/{image_id}")
async def delete_image(image_id: str):
    """
    Delete an image. (This is a placeholder and does not delete from the main backend yet)
    """
    # TODO: Implement deletion by calling the main backend's delete API
    return {"message": f"Image '{image_id}' deletion placeholder."}