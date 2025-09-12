import os
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

import schemas_legacy as schemas
from config import settings
from dependencies import get_current_user

router = APIRouter(
    prefix="/models",
    tags=["models"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

def get_models_from_dir(directory: Path, allowed_extensions: List[str]) -> List[schemas.ModelInfo]:
    models = []
    if not directory.is_dir():
        return models
    for item in directory.iterdir():
        if item.is_file() and item.suffix in allowed_extensions:
            models.append(schemas.ModelInfo(name=item.name, path=str(item)))
    return models

@router.get("/checkpoints", response_model=List[schemas.ModelInfo])
def list_checkpoints():
    """
    Get a list of available checkpoint models.
    """
    allowed_extensions = [".safetensors", ".ckpt"]
    models_dir = Path(settings.COMFYUI_MODELS_DIR)
    return get_models_from_dir(models_dir, allowed_extensions)

@router.get("/loras", response_model=List[schemas.ModelInfo])
def list_loras():
    """
    Get a list of available LoRA models.
    """
    allowed_extensions = [".safetensors", ".pt"]
    loras_dir = Path(settings.COMFYUI_LORAS_DIR)
    return get_models_from_dir(loras_dir, allowed_extensions)

@router.post("/upload/{model_type}")
async def upload_model(model_type: str, file: UploadFile = File(...)):
    """
    Upload a model file (checkpoint or LoRA).
    """
    if model_type not in ["checkpoints", "loras"]:
        raise HTTPException(status_code=400, detail="Invalid model type specified.")

    target_dir = Path(settings.COMFYUI_MODELS_DIR) if model_type == "checkpoints" else Path(settings.COMFYUI_LORAS_DIR)
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / file.filename
    if file_path.exists():
        raise HTTPException(status_code=400, detail=f"File '{file.filename}' already exists.")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        file.file.close()

    return {"filename": file.filename, "path": str(file_path)}

@router.delete("/{model_type}/{model_name}")
def delete_model(model_type: str, model_name: str):
    """
    Delete a model file.
    """
    if model_type not in ["checkpoints", "loras"]:
        raise HTTPException(status_code=400, detail="Invalid model type specified.")

    target_dir = Path(settings.COMFYUI_MODELS_DIR) if model_type == "checkpoints" else Path(settings.COMFYUI_LORAS_DIR)
    file_path = target_dir / model_name

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found.")

    try:
        os.remove(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not delete file: {e}")

    return {"message": f"Model '{model_name}' deleted successfully."}