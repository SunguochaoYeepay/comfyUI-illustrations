#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
负责SQLite数据库的初始化和操作
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional


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
                is_favorited INTEGER DEFAULT 0
            )
        """)
        
        # 检查是否需要添加字段（兼容旧数据库）
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'progress' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0")
        if 'is_favorited' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN is_favorited INTEGER DEFAULT 0")
        
        conn.commit()
        conn.close()
    
    def create_task(self, task_id: str, description: str, reference_image_path: str, parameters: Dict[str, Any]) -> None:
        """创建任务记录
        
        Args:
            task_id: 任务ID
            description: 任务描述
            reference_image_path: 参考图像路径
            parameters: 任务参数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (id, status, description, reference_image_path, parameters, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, "pending", description, reference_image_path, 
            json.dumps(parameters), datetime.now(), datetime.now()
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
            return dict(zip(columns, row))
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
        # 构建查询条件
        query_conditions = []
        query_params = []
        
        # 处理收藏筛选
        if favorite_filter and favorite_filter != "all":
            if favorite_filter == "favorite":
                query_conditions.append("is_favorited = ?")
                query_params.append(1)
            elif favorite_filter == "not_favorite":
                query_conditions.append("is_favorited = ?")
                query_params.append(0)
        
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
                query_conditions.append("created_at >= ?")
                query_params.append(start_time.isoformat())
        
        # 构建WHERE子句
        where_clause = ""
        if query_conditions:
            where_clause = "WHERE " + " AND ".join(query_conditions)
        
        # 获取总数
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        count_query = f"SELECT COUNT(*) FROM tasks {where_clause}"
        cursor.execute(count_query, query_params)
        total_count = cursor.fetchone()[0]
        
        # 获取分页数据
        order_clause = "ORDER BY created_at DESC" if order == "desc" else "ORDER BY created_at ASC"
        limit_clause = f"LIMIT {limit} OFFSET {offset}"
        
        query = f"""
            SELECT id, status, description, reference_image_path, parameters, 
                   prompt_id, result_path, error, progress, created_at, updated_at, is_favorited
            FROM tasks 
            {where_clause}
            {order_clause}
            {limit_clause}
        """
        
        cursor.execute(query, query_params)
        rows = cursor.fetchall()
        conn.close()
        
        # 处理结果
        tasks = []
        for row in rows:
            columns = ['id', 'status', 'description', 'reference_image_path', 'parameters', 
                      'prompt_id', 'result_path', 'error', 'progress', 'created_at', 'updated_at', 'is_favorited']
            task = dict(zip(columns, row))
            
            # 解析参数
            try:
                task['parameters'] = json.loads(task['parameters']) if task['parameters'] else {}
            except:
                task['parameters'] = {}
            
            # 处理结果路径
            if task['result_path']:
                try:
                    result_paths = json.loads(task['result_path'])
                    if isinstance(result_paths, list):
                        task['image_count'] = len(result_paths)
                        task['image_urls'] = [f"/api/image/{task['id']}?index={i}" for i in range(len(result_paths))]
                    else:
                        task['image_count'] = 1
                        task['image_urls'] = [f"/api/image/{task['id']}"]
                except:
                    task['image_count'] = 1
                    task['image_urls'] = [f"/api/image/{task['id']}"]
            else:
                task['image_count'] = 0
                task['image_urls'] = []
            
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
        """切换任务收藏状态
        
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
