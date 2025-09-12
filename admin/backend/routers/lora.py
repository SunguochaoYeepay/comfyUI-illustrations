from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
from typing import List, Optional
import shutil
import json
import time
from pathlib import Path
from config import settings
from pydantic import BaseModel

router = APIRouter()

# 1. Updated LoraMeta schema
class LoraMeta(BaseModel):
    display_name: Optional[str] = None
    base_model: Optional[str] = None
    description: Optional[str] = None
    new_name: Optional[str] = None

class LoraCreate(BaseModel):
    filename: str
    display_name: str
    base_model: Optional[str] = None
    description: Optional[str] = None

def get_lora_metadata(lora_path: Path):
    """从 .json 文件, .safetensors 元数据, 或文件名推断LoRA元数据"""
    meta = {
        "base_model": "未知",
        "description": "",
        "preview_path": None,
        "display_name": lora_path.name
    }
    json_path = lora_path.with_suffix('.json')
    preview_path = lora_path.with_suffix('.png')

    # 1. 尝试从 .json 文件读取
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                json_data = json.load(f)
                meta["display_name"] = json_data.get("display_name", meta["display_name"])
                meta["base_model"] = json_data.get("base_model", meta["base_model"])
                meta["description"] = json_data.get("description", meta["description"])
                meta["created_at"] = json_data.get("created_at")
                meta["modified_at"] = json_data.get("modified_at")
            except json.JSONDecodeError:
                pass # JSON 文件损坏则忽略
    else:
        # For unmanaged models, set timestamps to None initially
        meta["created_at"] = None
        meta["modified_at"] = None

    # 2. 如果 .json 中没有 base_model，尝试从 .safetensors 元数据读取
    if meta["base_model"] == "未知" and lora_path.suffix.lower() == '.safetensors':
        try:
            with open(lora_path, 'rb') as f:
                header_len = int.from_bytes(f.read(8), 'little')
                metadata_json = f.read(header_len)
                metadata = json.loads(metadata_json)
                if '__metadata__' in metadata and 'ss_sd_model_name' in metadata['__metadata__']:
                    meta["base_model"] = metadata['__metadata__']['ss_sd_model_name']
        except Exception:
            pass # 出错则忽略

    # 3. 如果仍然未知，尝试从文件名推断
    if meta["base_model"] == "未知":
        lora_name_lower = lora_path.name.lower()
        if "sdxl" in lora_name_lower:
            meta["base_model"] = "sdxl (推断)"
        elif "sd1.5" in lora_name_lower or "sd15" in lora_name_lower:
            meta["base_model"] = "sd1.5 (推断)"

    # 4. 检查预览图是否存在
    if preview_path.exists():
        meta["preview_path"] = f"/loras/preview/{preview_path.name}"

    return meta

@router.get("/loras", summary="获取LoRA模型列表")
async def get_loras(
    page: int = Query(1, ge=1), 
    page_size: int = Query(10, ge=1),
    name: Optional[str] = Query(None)
):
    if not settings.COMFYUI_LORAS_DIR.exists():
        return {"code": 404, "message": "LoRA目录未找到", "data": {"items": [], "total": 0, "page": page, "pageSize": page_size}}

    # 1. Get all potential lora files and their metadata for sorting
    lora_infos = []
    all_files = [f for f in settings.COMFYUI_LORAS_DIR.iterdir() if f.is_file() and f.suffix.lower() in ['.safetensors', '.ckpt', '.pt']]

    for file_path in all_files:
        stat_info = file_path.stat()
        meta = get_lora_metadata(file_path)
        
        # Use 'modified_at' from our managed metadata if available, otherwise fallback to file system mtime
        sort_key_time = meta.get("modified_at") or stat_info.st_mtime
        
        lora_infos.append({
            'path': file_path, 
            'sort_time': sort_key_time,
            'stat_info': stat_info,
            'meta': meta
        })

    # 1.5. Filter by name if provided
    if name:
        name_lower = name.lower()
        lora_infos = [
            info for info in lora_infos
            if name_lower in info['path'].name.lower() or \
               (info['meta'].get('display_name') and name_lower in info['meta']['display_name'].lower())
        ]

    # 2. Sort the list based on the definitive modification time
    lora_infos.sort(key=lambda x: x['sort_time'], reverse=True)

    # 3. Perform pagination
    total = len(lora_infos)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_loras_info = lora_infos[start:end]

    # 4. Generate the full response for paginated items
    loras = []
    for info in paginated_loras_info:
        file_path = info['path']
        stat_info = info['stat_info']
        meta = info['meta']
        json_path = file_path.with_suffix('.json')
        
        created_ts = meta.get("created_at") or stat_info.st_ctime
        modified_ts = meta.get("modified_at") or stat_info.st_mtime

        loras.append({
            "name": file_path.name,
            "display_name": meta["display_name"],
            "is_managed": json_path.exists(),
            "size": stat_info.st_size,
            "created": time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(created_ts)),
            "modified": time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(modified_ts)),
            "base_model": meta["base_model"],
            "description": meta["description"],
            "preview_url": meta["preview_path"]
        })
        
    return {"code": 200, "message": "获取成功", "data": {"items": loras, "total": total, "page": page, "pageSize": page_size}}

@router.get("/loras/unassociated", summary="获取未关联的LoRA模型文件列表")
async def get_unassociated_loras():
    if not settings.COMFYUI_LORAS_DIR.exists():
        raise HTTPException(status_code=404, detail="LoRA目录未找到")

    model_files = [f for f in settings.COMFYUI_LORAS_DIR.iterdir() if f.is_file() and f.suffix.lower() in ['.safetensors', '.ckpt', '.pt']]
    
    unassociated_files = []
    for model_file in model_files:
        json_path = model_file.with_suffix('.json')
        if not json_path.exists():
            unassociated_files.append(model_file.name)

    return {"code": 200, "message": "获取成功", "data": sorted(unassociated_files)}

@router.post("/loras/create", summary="为现有模型文件创建LoRA记录")
async def create_lora_record(data: LoraCreate):
    lora_path = settings.COMFYUI_LORAS_DIR / data.filename
    if not lora_path.exists():
        raise HTTPException(status_code=404, detail="LoRA模型文件未找到")

    json_path = lora_path.with_suffix('.json')
    if json_path.exists():
        raise HTTPException(status_code=400, detail="该模型已存在LoRA记录")

    current_time = int(time.time())
    new_meta = {
        "display_name": data.display_name,
        "base_model": data.base_model,
        "description": data.description,
        "created_at": current_time,
        "modified_at": current_time,
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(new_meta, f, ensure_ascii=False, indent=4)

    return {"message": "LoRA记录创建成功", "filename": data.filename}


@router.post("/loras/{lora_name}/meta", summary="更新LoRA元数据")
async def update_lora_meta(lora_name: str, meta: LoraMeta):
    lora_path = settings.COMFYUI_LORAS_DIR / lora_name
    if not lora_path.exists():
        raise HTTPException(status_code=404, detail="LoRA模型文件未找到")

    json_path = lora_path.with_suffix('.json')
    preview_path = lora_path.with_suffix('.png')
    
    # Handle filename change (rename or re-associate)
    if meta.new_name and meta.new_name != lora_name:
        new_lora_path = settings.COMFYUI_LORAS_DIR / meta.new_name
        
        # Case 1: Re-associating with an existing file
        if new_lora_path.exists():
            new_json_path = new_lora_path.with_suffix('.json')
            if new_json_path.exists():
                raise HTTPException(status_code=400, detail=f"无法切换，因为目标模型 '{meta.new_name}' 已经有关联的元数据。")
            
            # Move metadata and preview files to the new association
            if json_path.exists():
                json_path.rename(new_json_path)
            if preview_path.exists():
                preview_path.rename(new_lora_path.with_suffix('.png'))
            
            # Update path variables for the rest of the function
            lora_path = new_lora_path
            json_path = new_json_path
        
        # Case 2: Renaming the file to a new name
        else:
            lora_path.rename(new_lora_path)
            if json_path.exists():
                json_path.rename(new_lora_path.with_suffix('.json'))
            if preview_path.exists():
                preview_path.rename(new_lora_path.with_suffix('.png'))
            
            # Update path variables
            lora_path = new_lora_path
            json_path = new_lora_path.with_suffix('.json')

    current_meta = {}
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                current_meta = json.load(f)
            except json.JSONDecodeError:
                pass

    # Update or set metadata content
    current_meta["display_name"] = meta.display_name if meta.display_name is not None else current_meta.get("display_name", lora_path.name)
    current_meta["base_model"] = meta.base_model if meta.base_model is not None else current_meta.get("base_model")
    current_meta["description"] = meta.description if meta.description is not None else current_meta.get("description")

    # Update modified time, and set created time if it's the first time
    current_meta["modified_at"] = int(time.time())
    if "created_at" not in current_meta:
        # If creating the .json for the first time, set created_at.
        # Fallback to file system's ctime, or use current time if file doesn't exist yet.
        try:
            stat_info = lora_path.stat()
            current_meta["created_at"] = int(stat_info.st_ctime)
        except FileNotFoundError:
            current_meta["created_at"] = current_meta["modified_at"]

    # Ensure a json file is created even if it didn't exist before (e.g. for unmanaged -> managed)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(current_meta, f, ensure_ascii=False, indent=4)

    return {"message": "元数据更新成功"}

@router.post("/loras/{lora_name}/preview", summary="上传LoRA预览图")
async def upload_lora_preview(lora_name: str, file: UploadFile = File(...)):
    lora_path = settings.COMFYUI_LORAS_DIR / lora_name
    if not lora_path.exists():
        raise HTTPException(status_code=404, detail="LoRA模型文件未找到")

    preview_path = lora_path.with_suffix('.png')

    try:
        with preview_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览图上传失败: {e}")

    return {"message": "预览图上传成功", "preview_url": f"/loras/preview/{preview_path.name}"}

@router.post("/loras/upload", summary="上传LoRA模型")
async def upload_lora(file: UploadFile = File(...)):
    allowed_extensions = {".safetensors", ".ckpt", ".pt"}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="文件格式不支持")

    file_path = settings.COMFYUI_LORAS_DIR / file.filename
    if file_path.exists():
        raise HTTPException(status_code=400, detail="同名文件已存在")

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {e}")

    return {"message": "LoRA模型上传成功", "filename": file.filename}

@router.delete("/loras/{lora_name}", summary="删除LoRA模型元数据")
async def delete_lora(lora_name: str):
    file_path = settings.COMFYUI_LORAS_DIR / lora_name
    
    json_path = file_path.with_suffix('.json')
    preview_path = file_path.with_suffix('.png')

    if not json_path.exists() and not preview_path.exists():
        raise HTTPException(status_code=404, detail="该模型没有关联的元数据或预览图可以删除")

    try:
        if json_path.exists():
            json_path.unlink()
        if preview_path.exists():
            preview_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"元数据文件删除失败: {e}")

    return {"message": "LoRA模型元数据删除成功", "filename": lora_name}