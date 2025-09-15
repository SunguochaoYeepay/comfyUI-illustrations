#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查工作流JSON格式的工具
"""

import json
import sys

def check_workflow_format(file_path):
    """检查工作流JSON格式"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ JSON文件解析成功: {file_path}")
        
        # 检查必需字段
        required_fields = ['nodes', 'connections']
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            else:
                print(f"✅ 找到字段: {field}")
        
        if missing_fields:
            print(f"❌ 缺少必需字段: {', '.join(missing_fields)}")
            return False
        
        # 检查字段类型
        if not isinstance(data['nodes'], dict):
            print("❌ 'nodes' 字段应该是字典类型")
            return False
        
        if not isinstance(data['connections'], list):
            print("❌ 'connections' 字段应该是列表类型")
            return False
        
        # 检查节点结构
        print(f"📊 节点数量: {len(data['nodes'])}")
        print(f"📊 连接数量: {len(data['connections'])}")
        
        # 显示节点类型
        node_types = {}
        for node_id, node in data['nodes'].items():
            class_type = node.get('class_type', 'Unknown')
            if class_type not in node_types:
                node_types[class_type] = 0
            node_types[class_type] += 1
        
        print("📋 节点类型统计:")
        for class_type, count in node_types.items():
            print(f"  - {class_type}: {count}个")
        
        print("✅ 工作流格式检查通过！")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python check_workflow_format.py <json文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    check_workflow_format(file_path)
