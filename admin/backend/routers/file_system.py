from fastapi import APIRouter, Query, HTTPException, Depends
import os
from pydantic import BaseModel
from typing import List, Optional
from config import settings, Settings

router = APIRouter()

def get_settings():
    return settings

class FileNode(BaseModel):
    name: str
    path: str
    is_dir: bool

@router.get("/fs/browse", response_model=List[FileNode], summary="浏览服务器文件目录")
def browse_files(relative_path: Optional[str] = Query(None, description="相对于模型根目录的路径"), settings: Settings = Depends(get_settings)):
    """
    浏览指定路径下的文件和目录。

    - **relative_path**: 要浏览的相对路径。如果未提供，则浏览模型根目录。
    """
    try:
        MODELS_BASE_DIR = str(settings.YEEPAY_MODELS_DIR)
        # 构造绝对路径
        if relative_path:
            # 替换前端可能传递的斜杠
            safe_relative_path = relative_path.replace("/", "\\")
            # 移除开头的斜杠，以防止构造出错误的绝对路径
            if safe_relative_path.startswith("\\"):
                safe_relative_path = safe_relative_path[1:]
            
            browse_path = os.path.join(MODELS_BASE_DIR, safe_relative_path)
        else:
            browse_path = MODELS_BASE_DIR

        # 安全检查：确保请求的路径在根目录之内，防止目录遍历攻击
        if not os.path.abspath(browse_path).startswith(os.path.abspath(MODELS_BASE_DIR)):
            raise HTTPException(status_code=403, detail="禁止访问！")

        if not os.path.exists(browse_path) or not os.path.isdir(browse_path):
            raise HTTPException(status_code=404, detail="路径不存在或不是一个目录")

        items = []
        for item in os.listdir(browse_path):
            item_path = os.path.join(browse_path, item)
            is_dir = os.path.isdir(item_path)
            
            # 计算返回给前端的相对路径
            display_path = os.path.join(relative_path, item) if relative_path else item

            items.append(FileNode(name=item, path=display_path.replace("\\", "/"), is_dir=is_dir))
        
        return items

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"浏览文件时发生错误: {str(e)}")