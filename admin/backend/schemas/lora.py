from pydantic import BaseModel, Field
from typing import Optional
import datetime

class LoraBase(BaseModel):
    name: str = Field(..., description="LoRA文件名（唯一标识）")
    display_name: str = Field(..., description="显示名称")
    base_model: str = Field(..., description="基础模型名称")
    description: Optional[str] = Field(None, description="LoRA描述")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    is_available: bool = Field(True, description="是否可用")
    is_managed: bool = Field(False, description="是否已管理")

class LoraCreate(LoraBase):
    pass

class LoraUpdate(BaseModel):
    name: Optional[str] = Field(None, description="LoRA文件名（唯一标识）")
    display_name: Optional[str] = Field(None, description="显示名称")
    base_model: Optional[str] = Field(None, description="基础模型名称")
    description: Optional[str] = Field(None, description="LoRA描述")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    is_available: Optional[bool] = Field(None, description="是否可用")
    is_managed: Optional[bool] = Field(None, description="是否已管理")

class Lora(LoraBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
