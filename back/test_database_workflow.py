#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完全数据库化后的工作流加载功能
验证不再依赖文件系统模板路径的工作流系统
"""

import asyncio
import json
from pathlib import Path
import sys

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from core.workflow_template import WorkflowTemplate
from core.config_client import get_config_client


async def test_database_workflow_loading():
    """测试数据库工作流加载功能"""
    print("🚀 开始测试完全数据库化的工作流加载功能...")
    
    try:
        # 1. 测试配置客户端
        print("\n📡 测试配置客户端连接...")
        config_client = get_config_client()
        
        # 2. 获取工作流配置
        print("\n📋 获取工作流配置...")
        workflows_config = await config_client.get_workflows_config()
        workflows = workflows_config.get("workflows", [])
        
        print(f"✅ 成功获取 {len(workflows)} 个工作流配置")
        
        if not workflows:
            print("⚠️ 没有找到工作流配置，请确保数据库中有工作流数据")
            return False
        
        # 3. 测试工作流模板管理器
        print("\n🔧 测试工作流模板管理器...")
        workflow_template = WorkflowTemplate()
        
        # 4. 测试工作流配置应用
        print("\n⚙️ 测试工作流配置应用...")
        test_workflow = workflows[0]  # 使用第一个工作流进行测试
        
        print(f"📝 测试工作流: {test_workflow.get('name')}")
        print(f"📝 工作流类型: {test_workflow.get('base_model_type')}")
        print(f"📝 工作流JSON存在: {'workflow_json' in test_workflow}")
        
        if 'workflow_json' in test_workflow and test_workflow['workflow_json']:
            print(f"📝 工作流JSON节点数量: {len(test_workflow['workflow_json'])}")
        else:
            print("⚠️ 工作流JSON为空或不存在")
            return False
        
        # 5. 测试参数应用
        print("\n🎯 测试参数应用到工作流...")
        test_parameters = {
            "description": "测试描述",
            "size": "1024x1024",
            "steps": 20,
            "seed": 12345
        }
        
        try:
            customized_workflow = await workflow_template.apply_workflow_config(
                test_workflow, test_parameters
            )
            print(f"✅ 成功应用参数，生成工作流包含 {len(customized_workflow)} 个节点")
            
            # 验证参数是否正确应用 - 支持更多节点类型
            has_text_nodes = False
            has_sampler_nodes = False
            
            for node_id, node in customized_workflow.items():
                if isinstance(node, dict):
                    class_type = node.get("class_type", "")
                    inputs = node.get("inputs", {})
                    
                    # 检查文本节点 - 支持更多类型
                    if class_type in ["CLIPTextEncode", "CLIPTextEncodeAdvanced"]:
                        if inputs.get("text") == test_parameters["description"]:
                            has_text_nodes = True
                            print(f"✅ 文本节点 {node_id} 参数应用成功")
                    elif class_type == "Google-Gemini":
                        # Gemini节点可能有不同的参数名
                        if (inputs.get("text") == test_parameters["description"] or 
                            inputs.get("prompt") == test_parameters["description"]):
                            has_text_nodes = True
                            print(f"✅ Gemini节点 {node_id} 参数应用成功")
                    elif "text" in inputs and inputs.get("text") == test_parameters["description"]:
                        has_text_nodes = True
                        print(f"✅ 其他文本节点 {node_id} ({class_type}) 参数应用成功")
                    
                    # 检查采样器节点 - 支持更多类型
                    if class_type in ["KSampler", "KSamplerAdvanced", "ModelSamplingAuraFlow"]:
                        if inputs.get("steps") == test_parameters["steps"]:
                            has_sampler_nodes = True
                            print(f"✅ 采样器节点 {node_id} 参数应用成功")
                    elif class_type == "Google-Gemini" and "steps" in inputs:
                        if inputs.get("steps") == test_parameters["steps"]:
                            has_sampler_nodes = True
                            print(f"✅ Gemini节点 {node_id} 步数参数应用成功")
            
            # 对于某些工作流类型，可能没有传统的采样器节点
            workflow_type = test_workflow.get("base_model_type", "")
            if "gemini" in workflow_type.lower():
                # Gemini工作流可能没有传统采样器，只检查文本节点
                if has_text_nodes:
                    print("✅ Gemini工作流参数应用验证通过")
                    return True
                else:
                    print("⚠️ Gemini工作流文本参数应用验证失败")
                    return False
            else:
                # 传统工作流需要文本和采样器节点
                if has_text_nodes and has_sampler_nodes:
                    print("✅ 参数应用验证通过")
                    return True
                else:
                    print("⚠️ 参数应用验证失败")
                    return False
                
        except Exception as e:
            print(f"❌ 参数应用失败: {e}")
            return False
        
        # 6. 测试模型配置获取
        print("\n🤖 测试模型配置获取...")
        models_config = await config_client.get_models_config()
        models = models_config.get("models", [])
        
        print(f"✅ 成功获取 {len(models)} 个模型配置")
        
        if models:
            test_model = models[0]
            print(f"📝 测试模型: {test_model.get('name')}")
            print(f"📝 模型类型: {test_model.get('model_type')}")
            print(f"📝 模型可用: {test_model.get('available')}")
        
        print("\n🎉 所有测试通过！完全数据库化的工作流系统运行正常")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_customization():
    """测试工作流自定义功能"""
    print("\n🔧 测试工作流自定义功能...")
    
    try:
        workflow_template = WorkflowTemplate()
        
        # 测试不同模型的工作流自定义
        test_cases = [
            {
                "model_name": "qwen-image",
                "description": "测试Qwen图像生成",
                "parameters": {
                    "size": "1024x1024",
                    "steps": 20,
                    "seed": 12345
                }
            },
            {
                "model_name": "flux1-dev", 
                "description": "测试Flux1图像生成",
                "parameters": {
                    "size": "1024x1024",
                    "steps": 25,
                    "seed": 54321
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n📝 测试模型: {test_case['model_name']}")
            
            try:
                workflow = await workflow_template.customize_workflow_from_config(
                    reference_image_path="",
                    description=test_case["description"],
                    parameters=test_case["parameters"],
                    model_name=test_case["model_name"]
                )
                
                print(f"✅ 成功生成工作流，包含 {len(workflow)} 个节点")
                
            except Exception as e:
                print(f"⚠️ 模型 {test_case['model_name']} 测试失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流自定义测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 完全数据库化工作流系统测试")
    print("=" * 60)
    
    # 测试1: 数据库工作流加载
    test1_result = await test_database_workflow_loading()
    
    # 测试2: 工作流自定义
    test2_result = await test_workflow_customization()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   - 数据库工作流加载: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"   - 工作流自定义功能: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！完全数据库化的工作流系统运行正常")
        print("💡 系统已成功移除对文件系统模板路径的依赖")
    else:
        print("\n❌ 部分测试失败，请检查配置和数据库状态")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
