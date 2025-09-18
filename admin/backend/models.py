import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    audit_logs = relationship("AdminAuditLog", back_populates="admin")

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"))
    action = Column(String(100), nullable=False)
    target_resource_id = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(JSON, nullable=True)

    admin = relationship("AdminUser", back_populates="audit_logs")

class Inspiration(Base):
    __tablename__ = "inspirations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False) # Assuming a user table exists in the main app
    image_id = Column(Integer, nullable=False) # Assuming an image table exists in the main app
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), nullable=False, unique=True)  # 不可变的系统标识符
    name = Column(String(100), nullable=False)  # 可变的显示名称
    description = Column(Text, nullable=True)
    workflow_json = Column(JSON, nullable=False)
    base_model_type = Column(String(50), nullable=True)  # 主要关联的基础模型类型
    status = Column(String(20), default="enabled", nullable=False)  # enabled, disabled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关联关系
    base_models = relationship("BaseModel", back_populates="workflow")

class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # 'positive' or 'negative'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BaseModel(Base):
    __tablename__ = "base_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200), nullable=False)  # 显示名称
    model_type = Column(String(50), nullable=False)     # 模型类型：flux, qwen, wan, gemini, seedream4
    description = Column(Text, nullable=True)
    unet_file = Column(String(255), nullable=True)      # 文件名而非路径
    clip_file = Column(String(255), nullable=True)      # 文件名而非路径
    vae_file = Column(String(255), nullable=True)       # 文件名而非路径
    # template_path 字段已移除，完全数据库化
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=True)  # 关联的工作流ID
    preview_image_path = Column(String(255), nullable=True)
    is_available = Column(Boolean, default=False)       # 可用性状态
    is_default = Column(Boolean, default=False)         # 是否为默认模型
    sort_order = Column(Integer, default=0)             # 排序顺序
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关联关系
    workflow = relationship("Workflow", back_populates="base_models")


class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Lora(Base):
    __tablename__ = "loras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    base_model = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    is_available = Column(Boolean, default=True)
    is_managed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)