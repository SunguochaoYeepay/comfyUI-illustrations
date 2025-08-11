#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证器 - 确保所有必要的配置都正确设置
避免运行时配置错误
"""

import os
from pathlib import Path
from typing import List, Dict, Any

from config.settings import (
    COMFYUI_URL, DB_PATH, UPLOAD_DIR, OUTPUT_DIR,
    COMFYUI_OUTPUT_DIR, COMFYUI_MAIN_OUTPUT_DIR, COMFYUI_INPUT_DIR,
    ENVIRONMENT
)


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


def validate_environment() -> Dict[str, Any]:
    """验证环境配置"""
    errors = []
    warnings = []
    
    # 检查环境变量
    if not ENVIRONMENT:
        errors.append("ENVIRONMENT 未设置")
    elif ENVIRONMENT not in ["local", "production"]:
        warnings.append(f"ENVIRONMENT 值不标准: {ENVIRONMENT}")
    
    # 检查ComfyUI配置
    if not COMFYUI_URL:
        errors.append("COMFYUI_URL 未设置")
    
    # 检查数据库路径
    if not DB_PATH:
        errors.append("DB_PATH 未设置")
    else:
        db_dir = Path(DB_PATH).parent
        if not db_dir.exists():
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"无法创建数据库目录 {db_dir}: {e}")
    
    # 检查目录配置
    directories = {
        "UPLOAD_DIR": UPLOAD_DIR,
        "OUTPUT_DIR": OUTPUT_DIR,
        "COMFYUI_OUTPUT_DIR": COMFYUI_OUTPUT_DIR,
        "COMFYUI_MAIN_OUTPUT_DIR": COMFYUI_MAIN_OUTPUT_DIR,
        "COMFYUI_INPUT_DIR": COMFYUI_INPUT_DIR,
    }
    
    for name, path in directories.items():
        if not path:
            errors.append(f"{name} 未设置")
            continue
        
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"无法创建目录 {name}={path}: {e}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "environment": ENVIRONMENT,
        "db_path": DB_PATH,
        "comfyui_url": COMFYUI_URL
    }


def ensure_valid_config():
    """确保配置有效，否则抛出异常"""
    result = validate_environment()
    
    if result["warnings"]:
        for warning in result["warnings"]:
            print(f"⚠️ 配置警告: {warning}")
    
    if not result["valid"]:
        error_msg = "配置验证失败:\n" + "\n".join(f"- {error}" for error in result["errors"])
        raise ConfigValidationError(error_msg)
    
    print(f"✅ 配置验证通过 (环境: {result['environment']})")
    return result


if __name__ == "__main__":
    # 直接运行时进行配置验证
    try:
        result = ensure_valid_config()
        print("🎉 所有配置验证通过")
    except ConfigValidationError as e:
        print(f"❌ {e}")
        exit(1)
