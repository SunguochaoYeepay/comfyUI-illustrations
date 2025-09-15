from pydantic import BaseModel
from typing import Optional, List
import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class AdminUserBase(BaseModel):
    username: str

class AdminUserCreate(AdminUserBase):
    password: str

class AdminUserInDB(AdminUserBase):
    id: int
    hashed_password: str
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class AdminUser(AdminUserBase):
    id: int
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class InspirationBase(BaseModel):
    user_id: int
    image_id: int

class InspirationCreate(InspirationBase):
    pass

class Inspiration(InspirationBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class InspirationUpdate(BaseModel):
    user_id: Optional[int] = None
    image_id: Optional[int] = None

class AdminAuditLogBase(BaseModel):
    admin_id: int
    action: str
    target_resource_id: Optional[str] = None
    details: Optional[dict] = None

class AdminAuditLogCreate(AdminAuditLogBase):
    pass

class AdminAuditLog(AdminAuditLogBase):
    id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

class ModelInfo(BaseModel):
    name: str
    path: str
    size: int

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_json: dict

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_json: Optional[dict] = None

class Workflow(WorkflowBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class PromptBase(BaseModel):
    name: str
    type: str
    content: str

class PromptCreate(PromptBase):
    pass

class Prompt(PromptBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True