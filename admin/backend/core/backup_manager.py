#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份管理器 - 核心备份和恢复逻辑
"""

import os
import sys
import json
import uuid
import shutil
import hashlib
import zipfile
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiofiles

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class BackupManager:
    """备份管理器"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.temp_dir = Path("temp_backups")
        self.project_root = Path(__file__).parent.parent.parent.parent
        
        # 创建必要目录
        self.backup_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # 备份路径配置
        self.main_service_paths = {
            "database": self.project_root / "back" / "tasks.db",
            "uploads": self.project_root / "back" / "uploads",
            "outputs": self.project_root / "back" / "outputs",
            "workflows": self.project_root / "back" / "workflows",
            "thumbnails": self.project_root / "back" / "thumbnails",
            "config": self.project_root / "back" / "config"
        }
        
        self.admin_service_paths = {
            "database": self.project_root / "admin" / "backend" / "admin.db",
            "uploads": self.project_root / "admin" / "uploads",
            "outputs": self.project_root / "admin" / "outputs",
            "config": self.project_root / "admin" / "backend" / "config.py"
        }
        
        self.system_paths = {
            "docker_compose": self.project_root / "docker-compose.yml",
            "docker_compose_prod": self.project_root / "docker-compose.prod.yml",
            "env_production": self.project_root / "env.production",
            "nginx": self.project_root / "nginx"
        }

    async def create_backup(self, backup_type: str, backup_name: str, 
                          description: str = "", compression_level: int = 6, 
                          include_files: bool = True) -> str:
        """创建备份"""
        backup_id = str(uuid.uuid4())
        
        print(f"🔄 开始创建备份: {backup_name} ({backup_id})")
        print(f"📋 备份类型: {backup_type}")
        
        try:
            # 验证备份类型
            if backup_type not in ["full", "main_service", "admin_service"]:
                raise ValueError(f"无效的备份类型: {backup_type}")
            
            # 创建临时备份目录
            temp_backup_path = self.temp_dir / f"{backup_name}_{backup_id}"
            temp_backup_path.mkdir(parents=True, exist_ok=True)
            
            # 创建备份元数据
            metadata = {
                "backup_id": backup_id,
                "backup_name": backup_name,
                "backup_type": backup_type,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            # 执行备份
            if backup_type == "full":
                await self._backup_main_service(temp_backup_path, include_files)
                await self._backup_admin_service(temp_backup_path)
                await self._backup_system_configs(temp_backup_path)
            elif backup_type == "main_service":
                await self._backup_main_service(temp_backup_path, include_files)
            elif backup_type == "admin_service":
                await self._backup_admin_service(temp_backup_path)
            
            # 保存元数据
            metadata_file = temp_backup_path / "backup_metadata.json"
            async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
            
            # 压缩备份
            archive_path = await self._compress_backup(temp_backup_path, backup_id, compression_level)
            
            # 计算校验和
            checksum = await self._calculate_checksum(archive_path)
            
            # 清理临时文件
            shutil.rmtree(temp_backup_path)
            
            print(f"✅ 备份创建成功: {archive_path}")
            print(f"📊 备份大小: {archive_path.stat().st_size / (1024*1024):.2f} MB")
            print(f"🔐 校验和: {checksum}")
            
            return backup_id
            
        except Exception as e:
            print(f"❌ 备份创建失败: {e}")
            # 清理临时文件
            if temp_backup_path.exists():
                shutil.rmtree(temp_backup_path)
            raise e

    async def _backup_main_service(self, backup_path: Path, include_files: bool = True):
        """备份主服务数据"""
        print("📦 备份主服务数据...")
        
        main_service_dir = backup_path / "main_service"
        main_service_dir.mkdir(exist_ok=True)
        
        # 定义文件目录（图片、视频、上传文件等）
        file_dirs = {'outputs', 'uploads', 'thumbnails'}
        
        for name, source_path in self.main_service_paths.items():
            # 如果设置了不包含文件，且当前目录是文件目录，则跳过
            if not include_files and name in file_dirs:
                print(f"  ⏭️ 跳过文件目录: {name} (仅备份数据)")
                continue
                
            if source_path.exists():
                dest_path = main_service_dir / name
                
                if source_path.is_file():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    print(f"  ✅ 已备份文件: {name}")
                elif source_path.is_dir():
                    shutil.copytree(source_path, dest_path)
                    file_count = self._count_files(source_path)
                    size_mb = self._get_dir_size_mb(source_path)
                    print(f"  ✅ 已备份目录: {name} ({file_count} 个文件, {size_mb:.2f} MB)")
            else:
                print(f"  ⚠️ 路径不存在，跳过: {name}")

    async def _backup_admin_service(self, backup_path: Path):
        """备份Admin服务数据"""
        print("📦 备份Admin服务数据...")
        
        admin_service_dir = backup_path / "admin_service"
        admin_service_dir.mkdir(exist_ok=True)
        
        for name, source_path in self.admin_service_paths.items():
            if source_path.exists():
                dest_path = admin_service_dir / name
                
                if source_path.is_file():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    print(f"  ✅ 已备份文件: {name}")
                elif source_path.is_dir():
                    shutil.copytree(source_path, dest_path)
                    print(f"  ✅ 已备份目录: {name} ({self._count_files(source_path)} 个文件)")
            else:
                print(f"  ⚠️ 路径不存在，跳过: {name}")

    async def _backup_system_configs(self, backup_path: Path):
        """备份系统配置"""
        print("📦 备份系统配置...")
        
        system_dir = backup_path / "system"
        system_dir.mkdir(exist_ok=True)
        
        for name, source_path in self.system_paths.items():
            if source_path.exists():
                dest_path = system_dir / name
                
                if source_path.is_file():
                    shutil.copy2(source_path, dest_path)
                    print(f"  ✅ 已备份配置: {name}")
                elif source_path.is_dir():
                    shutil.copytree(source_path, dest_path)
                    print(f"  ✅ 已备份配置目录: {name} ({self._count_files(source_path)} 个文件)")
            else:
                print(f"  ⚠️ 配置不存在，跳过: {name}")

    async def _compress_backup(self, source_path: Path, backup_id: str, compression_level: int) -> Path:
        """压缩备份文件"""
        print("🗜️ 压缩备份文件...")
        
        archive_name = f"backup_{backup_id}.zip"
        archive_path = self.backup_dir / archive_name
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zipf:
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_path)
                    zipf.write(file_path, arcname)
        
        return archive_path

    async def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        print("🔐 计算文件校验和...")
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()

    async def restore_backup(self, backup_id: str, restore_type: str) -> bool:
        """恢复备份"""
        print(f"🔄 开始恢复备份: {backup_id}")
        print(f"📋 恢复类型: {restore_type}")
        
        try:
            # 查找备份文件
            backup_file = self._find_backup_file(backup_id)
            if not backup_file:
                raise FileNotFoundError(f"备份文件不存在: {backup_id}")
            
            # 验证备份文件
            if not await self._validate_backup(backup_file):
                raise ValueError("备份文件损坏或无效")
            
            # 创建临时恢复目录
            temp_restore_path = self.temp_dir / f"restore_{backup_id}"
            temp_restore_path.mkdir(exist_ok=True)
            
            try:
                # 解压备份文件
                await self._extract_backup(backup_file, temp_restore_path)
                
                # 停止服务（如果需要）
                await self._stop_services_if_needed(restore_type)
                
                # 执行恢复
                if restore_type == "full":
                    await self._restore_main_service(temp_restore_path)
                    await self._restore_admin_service(temp_restore_path)
                    await self._restore_system_configs(temp_restore_path)
                elif restore_type == "main_service":
                    await self._restore_main_service(temp_restore_path)
                elif restore_type == "admin_service":
                    await self._restore_admin_service(temp_restore_path)
                
                # 重启服务（如果需要）
                await self._restart_services_if_needed(restore_type)
                
                print("✅ 备份恢复成功")
                return True
                
            finally:
                # 清理临时文件
                if temp_restore_path.exists():
                    shutil.rmtree(temp_restore_path)
                    
        except Exception as e:
            print(f"❌ 备份恢复失败: {e}")
            raise e

    def _find_backup_file(self, backup_id: str) -> Optional[Path]:
        """查找备份文件"""
        for file_path in self.backup_dir.glob(f"backup_{backup_id}.zip"):
            return file_path
        return None

    async def _validate_backup(self, backup_file: Path) -> bool:
        """验证备份文件"""
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # 检查是否有元数据文件
                if 'backup_metadata.json' not in zipf.namelist():
                    return False
                
                # 尝试读取元数据
                metadata_content = zipf.read('backup_metadata.json').decode('utf-8')
                metadata = json.loads(metadata_content)
                
                # 验证必要字段
                required_fields = ['backup_id', 'backup_name', 'backup_type', 'created_at']
                for field in required_fields:
                    if field not in metadata:
                        return False
                
                return True
                
        except Exception as e:
            print(f"备份验证失败: {e}")
            return False

    async def _extract_backup(self, backup_file: Path, extract_path: Path):
        """解压备份文件"""
        print("📂 解压备份文件...")
        
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            zipf.extractall(extract_path)

    async def _restore_main_service(self, restore_path: Path):
        """恢复主服务数据"""
        print("📦 恢复主服务数据...")
        
        main_service_dir = restore_path / "main_service"
        if not main_service_dir.exists():
            print("  ⚠️ 主服务数据不存在，跳过恢复")
            return
        
        for name, dest_path in self.main_service_paths.items():
            source_path = main_service_dir / name
            
            if source_path.exists():
                if source_path.is_file():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    print(f"  ✅ 已恢复文件: {name}")
                elif source_path.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                    print(f"  ✅ 已恢复目录: {name}")

    async def _restore_admin_service(self, restore_path: Path):
        """恢复Admin服务数据"""
        print("📦 恢复Admin服务数据...")
        
        admin_service_dir = restore_path / "admin_service"
        if not admin_service_dir.exists():
            print("  ⚠️ Admin服务数据不存在，跳过恢复")
            return
        
        for name, dest_path in self.admin_service_paths.items():
            source_path = admin_service_dir / name
            
            if source_path.exists():
                if source_path.is_file():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    print(f"  ✅ 已恢复文件: {name}")
                elif source_path.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                    print(f"  ✅ 已恢复目录: {name}")

    async def _restore_system_configs(self, restore_path: Path):
        """恢复系统配置"""
        print("📦 恢复系统配置...")
        
        system_dir = restore_path / "system"
        if not system_dir.exists():
            print("  ⚠️ 系统配置不存在，跳过恢复")
            return
        
        for name, dest_path in self.system_paths.items():
            source_path = system_dir / name
            
            if source_path.exists():
                if source_path.is_file():
                    shutil.copy2(source_path, dest_path)
                    print(f"  ✅ 已恢复配置: {name}")
                elif source_path.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                    print(f"  ✅ 已恢复配置目录: {name}")

    async def _stop_services_if_needed(self, restore_type: str):
        """停止相关服务"""
        print("⏸️ 停止相关服务...")
        # 这里可以添加停止服务的逻辑
        # 根据用户规则，需要确认后再执行
        print("  ℹ️ 服务停止需要管理员确认")

    async def _restart_services_if_needed(self, restore_type: str):
        """重启相关服务"""
        print("▶️ 重启相关服务...")
        # 这里可以添加重启服务的逻辑
        # 根据用户规则，需要确认后再执行
        print("  ℹ️ 服务重启需要管理员确认")

    def _count_files(self, directory: Path) -> int:
        """统计目录中的文件数量"""
        try:
            return sum(1 for _ in directory.rglob('*') if _.is_file())
        except:
            return 0
    
    def _get_dir_size_mb(self, path: Path) -> float:
        """获取目录大小（MB）"""
        if path.is_file():
            return path.stat().st_size / (1024 * 1024)
        
        total_size = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, PermissionError):
                    continue
        
        return total_size / (1024 * 1024)

    async def list_backups(self, page: int = 1, limit: int = 20, backup_type: str = "all") -> Dict[str, Any]:
        """获取备份列表"""
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.zip"):
            try:
                # 从文件名提取backup_id
                backup_id = backup_file.stem.replace("backup_", "")
                
                # 读取备份元数据
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if 'backup_metadata.json' in zipf.namelist():
                        metadata_content = zipf.read('backup_metadata.json').decode('utf-8')
                        metadata = json.loads(metadata_content)
                        
                        # 过滤备份类型
                        if backup_type != "all" and metadata.get('backup_type') != backup_type:
                            continue
                        
                        backup_info = {
                            "backup_id": backup_id,
                            "backup_name": metadata.get('backup_name', ''),
                            "backup_type": metadata.get('backup_type', ''),
                            "file_path": str(backup_file),
                            "backup_size": backup_file.stat().st_size,
                            "status": "completed",
                            "description": metadata.get('description', ''),
                            "created_at": metadata.get('created_at', ''),
                            "checksum": None  # 可以单独计算
                        }
                        
                        backups.append(backup_info)
                        
            except Exception as e:
                print(f"读取备份信息失败 {backup_file}: {e}")
                continue
        
        # 按创建时间排序
        backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 分页
        total = len(backups)
        start = (page - 1) * limit
        end = start + limit
        page_backups = backups[start:end]
        
        return {
            "backups": page_backups,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": end < total
        }

    async def delete_backup(self, backup_id: str) -> bool:
        """删除备份"""
        backup_file = self._find_backup_file(backup_id)
        if backup_file and backup_file.exists():
            backup_file.unlink()
            print(f"✅ 已删除备份文件: {backup_file}")
            return True
        return False

    async def cleanup_old_backups(self, retention_days: int = 30):
        """清理过期备份"""
        print(f"🧹 清理 {retention_days} 天前的备份...")
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        for backup_file in self.backup_dir.glob("backup_*.zip"):
            try:
                file_modified = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_modified < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    print(f"  🗑️ 已删除过期备份: {backup_file.name}")
                    
            except Exception as e:
                print(f"删除备份失败 {backup_file}: {e}")
        
        print(f"✅ 清理完成，共删除 {deleted_count} 个过期备份")
        return deleted_count
