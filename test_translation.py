#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译功能测试脚本 - 增强版
测试翻译准确性、性能和日志记录
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/translation_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def test_translation():
    """测试翻译功能"""
    
    # 测试文本 - 包含不同类型的文本
    test_texts = [
        # 图像生成提示词
        "一只可爱的橙色小猫坐在花园里，阳光明媚，高清摄影风格",
        "美丽的风景画，山水画风格，水墨画",
        "现代建筑，玻璃幕墙，城市夜景",
        
        # 艺术风格描述
        "油画风格，印象派，色彩鲜艳",
        "黑白摄影，复古风格，怀旧感",
        "科幻场景，未来城市，霓虹灯",
        
        # 技术术语
        "人工智能，机器学习，深度学习",
        "区块链技术，加密货币，去中心化",
        "云计算，大数据，物联网",
        
        # 日常用语
        "今天天气很好，适合出去散步",
        "我喜欢吃中餐，特别是川菜",
        "这个电影很好看，推荐大家去看"
    ]
    
    logger.info("🧪 开始翻译功能测试")
    logger.info(f"   测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   测试文本数量: {len(test_texts)}")
    
    async with aiohttp.ClientSession() as session:
        # 1. 测试健康检查
        logger.info("\n1. 测试翻译服务健康检查...")
        try:
            async with session.get("http://localhost:9000/api/translate/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"✅ 健康检查成功")
                    logger.info(f"   响应数据: {json.dumps(health_data, ensure_ascii=False, indent=2)}")
                    
                    if not health_data.get("translation_service_ready"):
                        logger.error("❌ 翻译服务不可用")
                        logger.error(f"   Ollama可用: {health_data.get('ollama_available')}")
                        logger.error(f"   qwen模型可用: {health_data.get('qwen_model_available')}")
                        return
                else:
                    logger.error(f"❌ 健康检查失败: {response.status}")
                    return
        except Exception as e:
            logger.error(f"❌ 健康检查异常: {e}")
            return
        
        # 2. 测试翻译功能
        logger.info("\n2. 测试翻译功能...")
        success_count = 0
        total_count = len(test_texts)
        
        for i, text in enumerate(test_texts, 1):
            logger.info(f"\n   测试 {i}/{total_count}: {text}")
            
            try:
                form_data = aiohttp.FormData()
                form_data.add_field('text', text)
                
                start_time = datetime.now()
                async with session.post("http://localhost:9000/api/translate", data=form_data) as response:
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            success_count += 1
                            logger.info(f"   ✅ 翻译成功 ({duration:.2f}秒)")
                            logger.info(f"   原文: {result['original']}")
                            logger.info(f"   译文: {result['translated']}")
                            logger.info(f"   字符比例: {len(result['translated'])}/{len(result['original'])}")
                        else:
                            logger.error(f"   ❌ 翻译失败: {result}")
                    else:
                        error_data = await response.json()
                        logger.error(f"   ❌ 翻译请求失败: {response.status} - {error_data}")
            except Exception as e:
                logger.error(f"   ❌ 翻译异常: {e}")
        
        # 3. 测试结果统计
        logger.info(f"\n3. 测试结果统计")
        logger.info(f"   总测试数: {total_count}")
        logger.info(f"   成功数: {success_count}")
        logger.info(f"   失败数: {total_count - success_count}")
        logger.info(f"   成功率: {(success_count/total_count)*100:.1f}%")
        
        if success_count == total_count:
            logger.info("🎉 所有测试通过！翻译功能正常")
        else:
            logger.warning(f"⚠️ 部分测试失败，需要检查翻译服务")

if __name__ == "__main__":
    asyncio.run(test_translation())
