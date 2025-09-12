from pydantic import BaseModel
from typing import Optional
import datetime

class BaseModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_file_path: str
    preview_image_path: Optional[str] = None

class BaseModelCreate(BaseModelBase):
    pass

class BaseModelUpdate(BaseModelBase):
    pass

class BaseModel(BaseModelBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True