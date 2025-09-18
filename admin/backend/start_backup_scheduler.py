#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动备份调度器
"""

import sys
import os
import asyncio
import signal

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.backup_scheduler import backup_scheduler

class BackupSchedulerService:
    """备份调度器服务"""
    
    def __init__(self):
        self.running = False
    
    async def start(self):
        """启动服务"""
        print("🚀 启动备份调度器服务...")
        
        try:
            # 启动备份调度器
            await backup_scheduler.start()
            self.running = True
            
            print("✅ 备份调度器服务已启动")
            print("📅 自动备份调度器正在运行...")
            
            # 保持服务运行
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⏹️ 收到停止信号，正在关闭服务...")
            await self.stop()
        except Exception as e:
            print(f"❌ 服务运行错误: {e}")
            await self.stop()
    
    async def stop(self):
        """停止服务"""
        if self.running:
            print("⏹️ 停止备份调度器服务...")
            await backup_scheduler.stop()
            self.running = False
            print("✅ 备份调度器服务已停止")

async def main():
    """主函数"""
    service = BackupSchedulerService()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        print(f"\n收到信号 {signum}，正在停止服务...")
        asyncio.create_task(service.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动服务
    await service.start()

if __name__ == "__main__":
    print("🔄 YeePay Admin 备份调度器")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)
