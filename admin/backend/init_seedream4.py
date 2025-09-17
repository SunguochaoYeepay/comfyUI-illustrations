#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化Seedream4 Volcano Engine基础模型和工作流
"""

import json
from database import SessionLocal
from models import BaseModel, Workflow

def init_seedream4():
    """初始化Seedream4基础模型和工作流"""
    db = SessionLocal()
    try:
        # 检查是否已存在Seedream4工作流
        existing_workflow = db.query(Workflow).filter(Workflow.name == "seedream4_volcano_engine").first()
        if existing_workflow:
            print("✅ Seedream4工作流已存在，跳过创建")
            return existing_workflow.id
        
        # 创建Seedream4工作流模板
        seedream4_workflow_json = {
            "11": {
                "inputs": {
                    "image": "generated-image-1758020573908.png"
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "加载图像"
                }
            },
            "12": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": [
                        "22",
                        0
                    ]
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "保存图像"
                }
            },
            "22": {
                "inputs": {
                    "prompt": "图1与图2合并，坐在一起由歌和福吉",
                    "size_preset": "2304x1728 (4:3)",
                    "width": 2048,
                    "height": 2048,
                    "seed": 559718440,
                    "image_input": [
                        "24",
                        0
                    ]
                },
                "class_type": "Seedream4_VolcEngine",
                "_meta": {
                    "title": "Seedream4 Volcano Engine"
                }
            },
            "24": {
                "inputs": {
                    "image1": [
                        "11",
                        0
                    ],
                    "image2": [
                        "25",
                        0
                    ]
                },
                "class_type": "ImageBatch",
                "_meta": {
                    "title": "图像组合批处理"
                }
            },
            "25": {
                "inputs": {
                    "image": "generated-image-1758020573908.png"
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "加载图像"
                }
            }
        }
        
        # 创建工作流记录
        workflow = Workflow(
            name="seedream4_volcano_engine",
            description="Seedream4 Volcano Engine图像融合工作流，支持两张图像的智能融合",
            workflow_json=seedream4_workflow_json,
            base_model_type="seedream4",
            status="enabled"
        )
        
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        
        print(f"✅ 创建Seedream4工作流成功，ID: {workflow.id}")
        
        # 检查是否已存在Seedream4基础模型
        existing_model = db.query(BaseModel).filter(BaseModel.name == "seedream4_volcano_engine").first()
        if existing_model:
            print("✅ Seedream4基础模型已存在，跳过创建")
            return workflow.id
        
        # 创建Seedream4基础模型
        base_model = BaseModel(
            name="seedream4_volcano_engine",
            display_name="Seedream4 Volcano Engine",
            model_type="seedream4",
            description="Seedream4 Volcano Engine图像融合模型，支持两张图像的智能融合，可以让人物坐在一起或进行其他融合效果",
            workflow_id=workflow.id,
            is_available=True,
            is_default=True,
            sort_order=7
        )
        
        db.add(base_model)
        db.commit()
        db.refresh(base_model)
        
        print(f"✅ 创建Seedream4基础模型成功，ID: {base_model.id}")
        print(f"📋 模型信息:")
        print(f"   - 名称: {base_model.display_name}")
        print(f"   - 类型: {base_model.model_type}")
        print(f"   - 描述: {base_model.description}")
        print(f"   - 工作流ID: {base_model.workflow_id}")
        print(f"   - 可用性: {base_model.is_available}")
        print(f"   - 默认模型: {base_model.is_default}")
        
        return workflow.id
        
    except Exception as e:
        print(f"❌ 初始化Seedream4失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def show_seedream4_models():
    """显示Seedream4模型信息"""
    db = SessionLocal()
    try:
        models = db.query(BaseModel).filter(BaseModel.model_type == "seedream4").all()
        if not models:
            print("❌ 未找到Seedream4模型")
            return
        
        print(f"📋 找到 {len(models)} 个Seedream4模型:")
        for model in models:
            print(f"   - ID: {model.id}")
            print(f"   - 名称: {model.display_name}")
            print(f"   - 类型: {model.model_type}")
            print(f"   - 可用性: {model.is_available}")
            print(f"   - 默认模型: {model.is_default}")
            print(f"   - 工作流ID: {model.workflow_id}")
            print("   ---")
            
    except Exception as e:
        print(f"❌ 查询Seedream4模型失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 开始初始化Seedream4 Volcano Engine...")
    init_seedream4()
    print("\n📊 Seedream4模型列表:")
    show_seedream4_models()
    print("✅ 初始化完成!")
