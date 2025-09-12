from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import shutil
from pathlib import Path
from config.settings import COMFYUI_LORAS_DIR

router = APIRouter()

@router.get("/loras", summary="获取LoRA模型列表")
async def get_loras():
    """
    获取所有可用的LoRA模型列表。
    """
    if not COMFYUI_LORAS_DIR.exists():
        return {"loras": []}
    
    loras = []
    for file_path in COMFYUI_LORAS_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.safetensors', '.ckpt', '.pt']:
            loras.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
            })
    return {"loras": loras}

@router.post("/loras/upload", summary="上传LoRA模型")
async def upload_lora(file: UploadFile = File(...)):
    """
    上传一个新的LoRA模型。
    """
    allowed_extensions = {".safetensors", ".ckpt", ".pt"}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="文件格式不支持，请上传.safetensors, .ckpt, 或 .pt文件")

    file_path = COMFYUI_LORAS_DIR / file.filename
    if file_path.exists():
        raise HTTPException(status_code=400, detail="同名文件已存在")

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {e}")

    return {"message": "LoRA模型上传成功", "filename": file.filename}

@router.delete("/loras/{lora_name}", summary="删除LoRA模型")
async def delete_lora(lora_name: str):
    """
    删除一个指定的LoRA模型。
    """
    file_path = COMFYUI_LORAS_DIR / lora_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件未找到")

    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件删除失败: {e}")

    return {"message": "LoRA模型删除成功", "filename": lora_name}