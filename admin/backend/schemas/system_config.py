from pydantic import BaseModel, Field
from typing import Optional
import datetime

class SystemConfigBase(BaseModel):
    key: str = Field(..., description="配置键")
    value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置描述")

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(SystemConfigBase):
    pass

class SystemConfig(SystemConfigBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
