#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
负责SQLite数据库的初始化和操作
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class DatabaseManager:
    """数据库管理器，负责SQLite数据库的初始化和操作"""
    
    def __init__(self, db_path: str):
        """初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                description TEXT,
                reference_image_path TEXT,
                parameters TEXT,
                prompt_id TEXT,
                result_path TEXT,
                error TEXT,
                progress INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                is_favorited INTEGER DEFAULT 0,
                task_type TEXT DEFAULT 'generate'
            )
        """)
        
        # 创建单张图片收藏表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                image_index INTEGER NOT NULL,
                filename TEXT,
                is_favorited INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(task_id, image_index)
            )
        """)
        
        # 检查是否需要添加字段（兼容旧数据库）
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'progress' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0")
        if 'is_favorited' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN is_favorited INTEGER DEFAULT 0")
        if 'task_type' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN task_type TEXT DEFAULT 'generate'")
        
        conn.commit()
        conn.close()
    
    def create_task(self, task_id: str, description: str, reference_image_path: str, parameters: Dict[str, Any], task_type: str = "generate") -> None:
        """创建任务记录
        
        Args:
            task_id: 任务ID
            description: 任务描述
            reference_image_path: 参考图像路径
            parameters: 任务参数
            task_type: 任务类型 ('generate' 或 'upscale')
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (id, status, description, reference_image_path, parameters, created_at, updated_at, task_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, "pending", description, reference_image_path, 
            json.dumps(parameters), datetime.now(), datetime.now(), task_type
        ))
        conn.commit()
        conn.close()
    
    def update_task_status(self, task_id: str, status: str, prompt_id: str = None, result_path: str = None, error: str = None) -> None:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            prompt_id: ComfyUI的prompt_id
            result_path: 结果文件路径
            error: 错误信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = ["status = ?", "updated_at = ?"]
        values = [status, datetime.now()]
        
        if prompt_id:
            update_fields.append("prompt_id = ?")
            values.append(prompt_id)
        if result_path:
            update_fields.append("result_path = ?")
            values.append(result_path)
        if error:
            update_fields.append("error = ?")
            values.append(error)
        
        values.append(task_id)
        
        cursor.execute(f"""
            UPDATE tasks SET {', '.join(update_fields)}
            WHERE id = ?
        """, values)
        conn.commit()
        conn.close()
    
    def update_task_progress(self, task_id: str, progress: int) -> None:
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks SET progress = ?, updated_at = ?
            WHERE id = ?
        """, (progress, datetime.now(), task_id))
        conn.commit()
        conn.close()
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息字典，如果不存在返回None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            task_data = dict(zip(columns, row))
            
            # 解析多图融合的reference_image_path（如果是JSON字符串）
            if task_data.get('reference_image_path'):
                try:
                    import json
                    # 尝试解析JSON字符串
                    parsed_paths = json.loads(task_data['reference_image_path'])
                    if isinstance(parsed_paths, list):
                        task_data['reference_image_path'] = parsed_paths
                except (json.JSONDecodeError, TypeError):
                    # 如果不是JSON字符串，保持原样
                    pass
            
            return task_data
        return None
    
    def get_tasks_with_filters(self, limit: int = 20, offset: int = 0, order: str = "desc", 
                              favorite_filter: str = None, time_filter: str = None) -> Dict[str, Any]:
        """获取任务列表（支持筛选）
        
        Args:
            limit: 限制数量
            offset: 偏移量
            order: 排序方式
            favorite_filter: 收藏筛选
            time_filter: 时间筛选
            
        Returns:
            包含任务列表和统计信息的字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 处理收藏筛选 - 支持单张图片收藏筛选
        if favorite_filter and favorite_filter != "all":
            if favorite_filter == "favorited":
                # 筛选包含收藏图片的任务
                query = """
                    SELECT DISTINCT t.id, t.status, t.description, t.reference_image_path, t.parameters, 
                           t.prompt_id, t.result_path, t.error, t.progress, t.created_at, t.updated_at, t.is_favorited, t.task_type
                    FROM tasks t
                    INNER JOIN image_favorites f ON t.id = f.task_id
                    WHERE f.is_favorited = 1
                """
                query_params = []
            elif favorite_filter == "not_favorite":
                # 筛选不包含收藏图片的任务
                query = """
                    SELECT t.id, t.status, t.description, t.reference_image_path, t.parameters, 
                           t.prompt_id, t.result_path, t.error, t.progress, t.created_at, t.updated_at, t.is_favorited, t.task_type
                    FROM tasks t
                    WHERE t.id NOT IN (
                        SELECT DISTINCT task_id FROM image_favorites WHERE is_favorited = 1
                    )
                """
                query_params = []
            else:
                # 任务级别的收藏筛选（向后兼容）
                query = """
                    SELECT id, status, description, reference_image_path, parameters, 
                           prompt_id, result_path, error, progress, created_at, updated_at, is_favorited, task_type
                    FROM tasks 
                    WHERE is_favorited = ?
                """
                query_params = [1 if favorite_filter == "favorite" else 0]
        else:
            # 没有收藏筛选
            query = """
                SELECT id, status, description, reference_image_path, parameters, 
                       prompt_id, result_path, error, progress, created_at, updated_at, is_favorited, task_type
                FROM tasks
            """
            query_params = []
        
        # 处理时间筛选
        if time_filter and time_filter != "all":
            from datetime import timedelta
            now = datetime.now()
            if time_filter == "today":
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_filter == "week":
                start_time = now - timedelta(days=7)
            elif time_filter == "month":
                start_time = now - timedelta(days=30)
            else:
                start_time = None
            
            if start_time:
                if "WHERE" in query:
                    query += " AND t.created_at >= ?"
                else:
                    query += " WHERE t.created_at >= ?"
                query_params.append(start_time.isoformat())
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, query_params)
        total_count = cursor.fetchone()[0]
        
        # 添加排序和分页
        # 根据查询是否包含JOIN来决定使用哪个表名
        if "INNER JOIN" in query or "NOT IN" in query:
            order_clause = "ORDER BY t.created_at ASC" if order == "asc" else "ORDER BY t.created_at DESC"
        else:
            order_clause = "ORDER BY created_at ASC" if order == "asc" else "ORDER BY created_at DESC"
        limit_clause = f"LIMIT {limit} OFFSET {offset}"
        
        final_query = f"{query} {order_clause} {limit_clause}"
        
        cursor.execute(final_query, query_params)
        rows = cursor.fetchall()
        conn.close()
        
        # 处理结果
        tasks = []
        for row in rows:
            columns = ['id', 'status', 'description', 'reference_image_path', 'parameters', 
                      'prompt_id', 'result_path', 'error', 'progress', 'created_at', 'updated_at', 'is_favorited', 'task_type']
            task = dict(zip(columns, row))
            
            # 解析多图融合的reference_image_path（如果是JSON字符串）
            if task.get('reference_image_path'):
                try:
                    # 尝试解析JSON字符串
                    parsed_paths = json.loads(task['reference_image_path'])
                    if isinstance(parsed_paths, list):
                        task['reference_image_path'] = parsed_paths
                except (json.JSONDecodeError, TypeError):
                    # 如果不是JSON字符串，保持原样
                    pass
            
            # 解析参数
            try:
                task['parameters'] = json.loads(task['parameters']) if task['parameters'] else {}
            except:
                task['parameters'] = {}
            
            # 处理结果路径和图片收藏状态
            if task['result_path']:
                try:
                    # 对于放大任务，结果路径是单个文件路径
                    if task.get('task_type') == 'upscale':
                        # 放大任务的结果路径是单个文件
                        image_path = Path(task['result_path'])
                        # 从路径中提取文件名
                        filename = image_path.name
                        task['image_count'] = 1
                        task['image_urls'] = [f"/api/upscale/image/{task['id']}/{filename}"]
                        # 为放大图片添加收藏状态
                        is_favorited = self.get_image_favorite_status(task['id'], 0)
                        task['images'] = [{
                            'task_id': task['id'],
                            'image_index': 0,
                            'url': f"/api/upscale/image/{task['id']}/{filename}",
                            'isFavorited': is_favorited
                        }]
                    else:
                        # 生成任务的结果路径是JSON数组
                        result_paths = json.loads(task['result_path'])
                        if isinstance(result_paths, list):
                            # 检查是否为视频任务
                            is_video_task = any(Path(path).suffix.lower() in ['.mp4', '.avi', '.mov', '.webm'] for path in result_paths)
                            
                            if is_video_task:
                                # 视频任务
                                task['image_count'] = 1
                                task['image_urls'] = [f"/api/video/{task['id']}"]
                                # 为视频添加收藏状态
                                is_favorited = self.get_image_favorite_status(task['id'], 0)
                                task['images'] = [{
                                    'task_id': task['id'],
                                    'image_index': 0,
                                    'url': f"/api/video/{task['id']}",
                                    'isFavorited': is_favorited
                                }]
                            else:
                                # 图片任务
                                task['image_count'] = len(result_paths)
                                task['image_urls'] = [f"/api/image/{task['id']}?index={i}" for i in range(len(result_paths))]
                                # 为每个图片添加收藏状态
                                task['images'] = []
                                for i in range(len(result_paths)):
                                    is_favorited = self.get_image_favorite_status(task['id'], i)
                                    task['images'].append({
                                        'task_id': task['id'],
                                        'image_index': i,
                                        'url': f"/api/image/{task['id']}?index={i}",
                                        'isFavorited': is_favorited
                                    })
                        else:
                            # 单个文件
                            is_video_file = Path(result_paths).suffix.lower() in ['.mp4', '.avi', '.mov', '.webm']
                            
                            if is_video_file:
                                # 单个视频文件
                                task['image_count'] = 1
                                task['image_urls'] = [f"/api/video/{task['id']}"]
                                # 为视频添加收藏状态
                                is_favorited = self.get_image_favorite_status(task['id'], 0)
                                task['images'] = [{
                                    'task_id': task['id'],
                                    'image_index': 0,
                                    'url': f"/api/video/{task['id']}",
                                    'isFavorited': is_favorited
                                }]
                            else:
                                # 单个图片文件
                                task['image_count'] = 1
                                task['image_urls'] = [f"/api/image/{task['id']}"]
                                # 为单个图片添加收藏状态
                                is_favorited = self.get_image_favorite_status(task['id'], 0)
                                task['images'] = [{
                                    'task_id': task['id'],
                                    'image_index': 0,
                                    'url': f"/api/image/{task['id']}",
                                    'isFavorited': is_favorited
                                }]
                except:
                    task['image_count'] = 1
                    task['image_urls'] = [f"/api/image/{task['id']}"]
                    # 为单个图片添加收藏状态
                    is_favorited = self.get_image_favorite_status(task['id'], 0)
                    task['images'] = [{
                        'task_id': task['id'],
                        'image_index': 0,
                        'url': f"/api/image/{task['id']}",
                        'isFavorited': is_favorited
                    }]
            else:
                task['image_count'] = 0
                task['image_urls'] = []
                task['images'] = []
            
            # 添加task_id字段以兼容前端
            task['task_id'] = task['id']
            
            tasks.append(task)
        
        # 计算是否有更多数据
        has_more = (offset + limit) < total_count
        
        return {
            "tasks": tasks,
            "total": total_count,
            "has_more": has_more,
            "limit": limit,
            "offset": offset,
            "order": order
        }
    
    def toggle_favorite(self, task_id: str) -> bool:
        """切换任务收藏状态（保留向后兼容）
        
        Args:
            task_id: 任务ID
            
        Returns:
            新的收藏状态
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取当前收藏状态
        cursor.execute("SELECT is_favorited FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False
        
        current_favorite = result[0]
        new_favorite = 0 if current_favorite else 1
        
        # 更新收藏状态
        cursor.execute("UPDATE tasks SET is_favorited = ?, updated_at = ? WHERE id = ?", 
                      (new_favorite, datetime.now(), task_id))
        conn.commit()
        conn.close()
        
        return bool(new_favorite)
    
    def toggle_image_favorite(self, task_id: str, image_index: int, filename: str = None) -> bool:
        """切换单张图片收藏状态
        
        Args:
            task_id: 任务ID
            image_index: 图片索引
            filename: 文件名（可选）
            
        Returns:
            新的收藏状态
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查是否已存在收藏记录
            cursor.execute("SELECT is_favorited FROM image_favorites WHERE task_id = ? AND image_index = ?", 
                          (task_id, image_index))
            result = cursor.fetchone()
            
            if result:
                # 更新现有记录
                current_favorite = result[0]
                new_favorite = 0 if current_favorite else 1
                cursor.execute("UPDATE image_favorites SET is_favorited = ?, updated_at = ? WHERE task_id = ? AND image_index = ?", 
                              (new_favorite, datetime.now(), task_id, image_index))
            else:
                # 创建新记录
                new_favorite = 1
                cursor.execute("INSERT INTO image_favorites (task_id, image_index, filename, is_favorited, created_at) VALUES (?, ?, ?, ?, ?)", 
                              (task_id, image_index, filename, new_favorite, datetime.now()))
            
            conn.commit()
            return bool(new_favorite)
        except Exception as e:
            print(f"切换图片收藏状态失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_image_favorite_status(self, task_id: str, image_index: int) -> bool:
        """获取单张图片的收藏状态
        
        Args:
            task_id: 任务ID
            image_index: 图片索引
            
        Returns:
            是否已收藏
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_favorited FROM image_favorites WHERE task_id = ? AND image_index = ?", 
                      (task_id, image_index))
        result = cursor.fetchone()
        
        conn.close()
        return bool(result[0]) if result else False
    
    def get_favorite_images(self) -> List[Dict[str, Any]]:
        """获取所有收藏的图片
        
        Returns:
            收藏图片列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 查询所有收藏的图片
        cursor.execute("""
            SELECT 
                t.id as task_id,
                t.description,
                t.created_at,
                t.parameters,
                t.result_path,
                t.reference_image_path,
                if.image_index,
                if.filename,
                if.is_favorited
            FROM tasks t
            INNER JOIN image_favorites if ON t.id = if.task_id
            WHERE if.is_favorited = 1
            ORDER BY if.created_at DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        favorites = []
        for row in results:
            task_id, description, created_at, parameters, result_path, reference_image_path, image_index, filename, is_favorited = row
            
            # 解析参数
            try:
                params = json.loads(parameters) if parameters else {}
            except:
                params = {}
            
            # 构建图片URL
            image_url = None
            if result_path:
                try:
                    # 尝试解析result_path为JSON数组
                    result_paths = json.loads(result_path)
                    if isinstance(result_paths, list) and image_index < len(result_paths):
                        image_url = f"/api/image/{task_id}?index={image_index}"
                    else:
                        # 单个文件
                        image_url = f"/api/image/{task_id}"
                except:
                    # 如果不是JSON，当作单个文件处理
                    image_url = f"/api/image/{task_id}"
            
            favorite_item = {
                "id": f"{task_id}_{image_index}",
                "task_id": task_id,
                "image_index": image_index,
                "title": description[:50] + "..." if description and len(description) > 50 else description or "未命名作品",
                "description": description or "暂无描述",
                "imageUrl": image_url,
                "prompt": description,
                "parameters": params,
                "createdAt": created_at,
                "filename": filename
            }
            
            favorites.append(favorite_item)
        
        return favorites

    
    def delete_task(self, task_id: str) -> Optional[str]:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            被删除任务的结果路径，如果任务不存在返回None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查任务是否存在
        cursor.execute("SELECT result_path FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return None
        
        result_path = result[0]
        
        # 删除数据库记录
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        
        return result_path
