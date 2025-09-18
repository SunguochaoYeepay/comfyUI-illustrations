from pydantic import BaseModel, Field
from typing import Optional
import datetime

class BaseModelBase(BaseModel):
    code: str = Field(..., description="不可变的系统标识符")
    name: str = Field(..., description="模型名称（唯一标识）")
    display_name: str = Field(..., description="显示名称")
    model_type: str = Field(..., description="模型类型：flux, qwen, wan, gemini, seedream4")
    description: Optional[str] = Field(None, description="模型描述")
    unet_file: Optional[str] = Field(None, description="UNet文件名")
    clip_file: Optional[str] = Field(None, description="CLIP文件名")
    vae_file: Optional[str] = Field(None, description="VAE文件名")
    # template_path 已移除，完全数据库化
    workflow_id: Optional[int] = Field(None, description="关联的工作流ID")
    preview_image_path: Optional[str] = Field(None, description="预览图路径")
    is_available: bool = Field(False, description="是否可用")
    is_default: bool = Field(False, description="是否为默认模型")
    sort_order: int = Field(0, description="排序顺序")

class BaseModelCreate(BaseModelBase):
    pass

class BaseModelUpdate(BaseModel):
    code: Optional[str] = Field(None, description="不可变的系统标识符")
    name: Optional[str] = Field(None, description="模型名称（唯一标识）")
    display_name: Optional[str] = Field(None, description="显示名称")
    model_type: Optional[str] = Field(None, description="模型类型：flux, qwen, wan, gemini")
    description: Optional[str] = Field(None, description="模型描述")
    unet_file: Optional[str] = Field(None, description="UNet文件名")
    clip_file: Optional[str] = Field(None, description="CLIP文件名")
    vae_file: Optional[str] = Field(None, description="VAE文件名")
    # template_path 已移除，完全数据库化
    workflow_id: Optional[int] = Field(None, description="关联的工作流ID")
    preview_image_path: Optional[str] = Field(None, description="预览图路径")
    is_available: Optional[bool] = Field(None, description="是否可用")
    is_default: Optional[bool] = Field(None, description="是否为默认模型")
    sort_order: Optional[int] = Field(None, description="排序顺序")

class BaseModel(BaseModelBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True