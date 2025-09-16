#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地配置文件管理模块
负责本地配置文件管理、配置模板生成、配置备份和恢复
"""

import json
import yaml
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger(__name__)


class LocalConfigManager:
    """本地配置文件管理器"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        初始化本地配置管理器
        
        Args:
            config_dir: 配置目录路径
        """
        self.config_dir = config_dir or Path(__file__).parent
        self.config_file = self.config_dir / "local_config.yaml"
        self.backup_dir = self.config_dir / "backups"
        
        # 确保目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化默认配置
        self._init_default_config()
    
    def _init_default_config(self):
        """初始化默认配置"""
        if not self.config_file.exists():
            default_config = self._get_default_config_template()
            self.save_config(default_config)
            logger.info("已创建默认本地配置文件")
    
    def _get_default_config_template(self) -> Dict[str, Any]:
        """获取默认配置模板"""
        return {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "models": {
                "models": [
                    {
                        "name": "qwen-image",
                        "display_name": "Qwen",
                        "model_type": "qwen",
                        "available": True,
                        "sort_order": 1,
                        "description": "千问图像模型，支持单图生成和多图融合"
                    },
                    {
                        "name": "flux-dev",
                        "display_name": "Flux Kontext",
                        "model_type": "flux",
                        "available": True,
                        "sort_order": 2,
                        "description": "Flux Kontext开发版本，支持高质量图像生成"
                    },
                    # flux1基础模型已移除，只保留FLUX.1 Kontext
                    {
                        "name": "wan2.2-video",
                        "display_name": "Wan2.2 视频",
                        "model_type": "wan",
                        "available": True,
                        "sort_order": 4,
                        "description": "Wan2.2图像到视频模型，支持高质量视频生成"
                    },
                    {
                        "name": "gemini-image",
                        "display_name": "Nano Banana",
                        "model_type": "gemini",
                        "available": True,
                        "sort_order": 5,
                        "description": "Google Gemini图像编辑&融合，支持无图、1图、2图的智能合成"
                    }
                ]
            },
            "loras": {
                "loras": [],
                "grouped_by_model": {
                    "flux-dev": [],
                    "qwen-image": [],
                    "wan2.2-video": []
                }
            },
            "workflows": {
                "workflows": [
                    {
                        "id": 1,
                        "name": "qwen_image_generation",
                        "display_name": "Qwen图像生成",
                        "base_model_type": "qwen",
                        "workflow_type": "image_generation",
                        "template_path": "workflows/qwen_image_generation_workflow.json",
                        "available": True,
                        "description": "Qwen单图生成工作流"
                    },
                    {
                        "id": 2,
                        "name": "qwen_image_fusion",
                        "display_name": "Qwen图像融合",
                        "base_model_type": "qwen",
                        "workflow_type": "image_fusion",
                        "template_path": "workflows/qwen_image_fusion_workflow.json",
                        "available": True,
                        "description": "Qwen多图融合工作流"
                    },
                    {
                        # flux1工作流已移除，只保留FLUX.1 Kontext
                        "description": "Flux1基础模型工作流"
                    },
                    {
                        "id": 4,
                        "name": "flux_kontext_workflow",
                        "display_name": "Flux Kontext工作流",
                        "base_model_type": "flux",
                        "workflow_type": "image_generation",
                        "template_path": "flux_kontext_dev_basic.json",
                        "available": True,
                        "description": "Flux Kontext开发版本工作流"
                    },
                    {
                        "id": 5,
                        "name": "wan_video_workflow",
                        "display_name": "Wan视频生成",
                        "base_model_type": "wan",
                        "workflow_type": "video_generation",
                        "template_path": "workflows/wan2.2_video_generation_workflow.json",
                        "available": True,
                        "description": "Wan2.2视频生成工作流"
                    },
                    {
                        "id": 6,
                        "name": "gemini_workflow",
                        "display_name": "Gemini工作流",
                        "base_model_type": "gemini",
                        "workflow_type": "image_editing",
                        "template_path": "workflows/google/api_google_gemini_image.json",
                        "available": True,
                        "description": "Google Gemini图像编辑工作流"
                    }
                ]
            },
            "image_gen": {
                "default_size": {
                    "width": 1024,
                    "height": 1024
                },
                "size_ratios": ["1:1", "4:3", "3:4", "16:9", "9:16"],
                "default_steps": 20,
                "default_count": 1,
                "supported_formats": ["png", "jpg", "jpeg", "webp"],
                "quality_settings": {
                    "low": {"steps": 10, "cfg": 7.0},
                    "medium": {"steps": 20, "cfg": 8.0},
                    "high": {"steps": 30, "cfg": 9.0}
                }
            },
            "system": {
                "cache_ttl": 300,
                "sync_interval": 60,
                "max_retry_attempts": 3,
                "timeout": 10,
                "enable_auto_backup": True,
                "backup_retention_days": 7
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """加载本地配置"""
        try:
            if not self.config_file.exists():
                logger.warning("本地配置文件不存在，返回默认配置")
                return self._get_default_config_template()
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 验证配置格式
            if not self._validate_config(config):
                logger.warning("配置文件格式无效，返回默认配置")
                return self._get_default_config_template()
            
            return config
        except Exception as e:
            logger.error(f"加载本地配置失败: {e}")
            return self._get_default_config_template()
    
    def save_config(self, config: Dict[str, Any]):
        """保存本地配置"""
        try:
            # 更新版本和时间戳
            config["version"] = config.get("version", "1.0.0")
            config["last_updated"] = datetime.now().isoformat()
            
            # 验证配置
            if not self._validate_config(config):
                raise ValueError("配置格式无效")
            
            # 创建备份
            if self.config_file.exists():
                self._create_backup()
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info("本地配置已保存")
        except Exception as e:
            logger.error(f"保存本地配置失败: {e}")
            raise
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置格式"""
        required_sections = ["models", "loras", "workflows", "image_gen"]
        
        for section in required_sections:
            if section not in config:
                logger.error(f"缺少必需的配置节: {section}")
                return False
        
        # 验证模型配置
        if "models" in config and "models" in config["models"]:
            for model in config["models"]["models"]:
                required_fields = ["name", "display_name", "model_type", "available"]
                for field in required_fields:
                    if field not in model:
                        logger.error(f"模型配置缺少必需字段: {field}")
                        return False
        
        # 验证生图配置
        if "image_gen" in config:
            image_gen = config["image_gen"]
            if "default_size" not in image_gen or "width" not in image_gen["default_size"] or "height" not in image_gen["default_size"]:
                logger.error("生图配置缺少默认尺寸")
                return False
        
        return True
    
    def get_config_section(self, section: str) -> Optional[Dict[str, Any]]:
        """获取配置节"""
        config = self.load_config()
        return config.get(section)
    
    def update_config_section(self, section: str, data: Dict[str, Any]):
        """更新配置节"""
        config = self.load_config()
        config[section] = data
        self.save_config(config)
    
    def _create_backup(self):
        """创建配置备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"local_config_{timestamp}.yaml"
            shutil.copy2(self.config_file, backup_file)
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            logger.info(f"配置备份已创建: {backup_file}")
        except Exception as e:
            logger.error(f"创建配置备份失败: {e}")
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        try:
            retention_days = 7  # 默认保留7天
            config = self.load_config()
            if "system" in config and "backup_retention_days" in config["system"]:
                retention_days = config["system"]["backup_retention_days"]
            
            cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
            
            for backup_file in self.backup_dir.glob("local_config_*.yaml"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    logger.info(f"已删除旧备份: {backup_file}")
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
    
    def restore_from_backup(self, backup_file: Union[str, Path]) -> bool:
        """从备份恢复配置"""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            # 验证备份文件
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_config = yaml.safe_load(f)
            
            if not self._validate_config(backup_config):
                logger.error("备份文件格式无效")
                return False
            
            # 创建当前配置的备份
            if self.config_file.exists():
                self._create_backup()
            
            # 恢复配置
            shutil.copy2(backup_path, self.config_file)
            logger.info(f"配置已从备份恢复: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"从备份恢复配置失败: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        try:
            for backup_file in self.backup_dir.glob("local_config_*.yaml"):
                stat = backup_file.stat()
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # 按创建时间排序
            backups.sort(key=lambda x: x["created_at"], reverse=True)
        except Exception as e:
            logger.error(f"列出备份失败: {e}")
        
        return backups
    
    def export_config(self, export_path: Union[str, Path], format: str = "yaml") -> bool:
        """导出配置"""
        try:
            export_path = Path(export_path)
            config = self.load_config()
            
            if format.lower() == "json":
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            else:  # yaml
                with open(export_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"配置已导出: {export_path}")
            return True
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: Union[str, Path]) -> bool:
        """导入配置"""
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                logger.error(f"导入文件不存在: {import_path}")
                return False
            
            # 读取配置
            if import_path.suffix.lower() == ".json":
                with open(import_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:  # yaml
                with open(import_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            
            # 验证配置
            if not self._validate_config(config):
                logger.error("导入的配置文件格式无效")
                return False
            
            # 保存配置
            self.save_config(config)
            logger.info(f"配置已导入: {import_path}")
            return True
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        config = self.load_config()
        config_file_stat = self.config_file.stat() if self.config_file.exists() else None
        
        return {
            "config_file": str(self.config_file),
            "config_dir": str(self.config_dir),
            "backup_dir": str(self.backup_dir),
            "version": config.get("version", "unknown"),
            "last_updated": config.get("last_updated", "unknown"),
            "file_size": config_file_stat.st_size if config_file_stat else 0,
            "file_modified": datetime.fromtimestamp(config_file_stat.st_mtime).isoformat() if config_file_stat else None,
            "backup_count": len(self.list_backups()),
            "sections": list(config.keys())
        }
    
    def generate_config_template(self, template_type: str = "full") -> Dict[str, Any]:
        """生成配置模板"""
        if template_type == "minimal":
            return {
                "version": "1.0.0",
                "models": {
                    "models": [
                        {
                            "name": "default-model",
                            "display_name": "Default Model",
                            "model_type": "default",
                            "available": True,
                            "sort_order": 1
                        }
                    ]
                },
                "loras": {"loras": [], "grouped_by_model": {}},
                "workflows": {"workflows": []},
                "image_gen": {
                    "default_size": {"width": 1024, "height": 1024},
                    "size_ratios": ["1:1"],
                    "default_steps": 20
                }
            }
        else:
            return self._get_default_config_template()


# 全局配置管理器实例
_local_config_manager: Optional[LocalConfigManager] = None


def get_local_config_manager() -> LocalConfigManager:
    """获取本地配置管理器实例"""
    global _local_config_manager
    if _local_config_manager is None:
        _local_config_manager = LocalConfigManager()
    return _local_config_manager


# 便捷函数
def load_local_config() -> Dict[str, Any]:
    """加载本地配置"""
    manager = get_local_config_manager()
    return manager.load_config()


def save_local_config(config: Dict[str, Any]):
    """保存本地配置"""
    manager = get_local_config_manager()
    manager.save_config(config)


def get_local_config_section(section: str) -> Optional[Dict[str, Any]]:
    """获取本地配置节"""
    manager = get_local_config_manager()
    return manager.get_config_section(section)


def update_local_config_section(section: str, data: Dict[str, Any]):
    """更新本地配置节"""
    manager = get_local_config_manager()
    manager.update_config_section(section, data)


def create_config_backup() -> bool:
    """创建配置备份"""
    manager = get_local_config_manager()
    try:
        manager._create_backup()
        return True
    except Exception:
        return False


def restore_config_from_backup(backup_file: Union[str, Path]) -> bool:
    """从备份恢复配置"""
    manager = get_local_config_manager()
    return manager.restore_from_backup(backup_file)


def list_config_backups() -> List[Dict[str, Any]]:
    """列出配置备份"""
    manager = get_local_config_manager()
    return manager.list_backups()


def export_local_config(export_path: Union[str, Path], format: str = "yaml") -> bool:
    """导出本地配置"""
    manager = get_local_config_manager()
    return manager.export_config(export_path, format)


def import_local_config(import_path: Union[str, Path]) -> bool:
    """导入本地配置"""
    manager = get_local_config_manager()
    return manager.import_config(import_path)


def get_local_config_info() -> Dict[str, Any]:
    """获取本地配置信息"""
    manager = get_local_config_manager()
    return manager.get_config_info()
