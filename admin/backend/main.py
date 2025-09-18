import sys
import os
import subprocess
import time

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def kill_process_on_port(port):
    """清理指定端口上的进程"""
    try:
        # 查找占用端口的进程
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
        lines = result.stdout.split('\n')
        
        pids_to_kill = []
        for line in lines:
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    pids_to_kill.append(pid)
        
        if pids_to_kill:
            print(f"🔧 发现端口 {port} 上的进程: {pids_to_kill}")
            for pid in pids_to_kill:
                try:
                    # 终止进程
                    subprocess.run(['taskkill', '/f', '/pid', pid], capture_output=True, shell=True)
                    print(f"✅ 已清理端口 {port} 上的进程 PID: {pid}")
                except Exception as e:
                    print(f"⚠️ 清理进程 {pid} 失败: {e}")
            
            # 等待所有进程完全终止
            print("⏳ 等待进程完全终止...")
            time.sleep(3)
            
            # 验证端口是否已释放
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
            remaining = [line for line in result.stdout.split('\n') if f':{port}' in line and 'LISTENING' in line]
            if remaining:
                print(f"⚠️ 端口 {port} 仍有进程在监听: {remaining}")
            else:
                print(f"✅ 端口 {port} 已完全释放")
        else:
            print(f"✅ 端口 {port} 没有被占用")
            
    except Exception as e:
        print(f"⚠️ 清理端口 {port} 失败: {e}")

# 启动前清理8888端口（仅在直接启动时，不在热重载时）
if __name__ == "__main__":
    print("🔧 正在清理端口8888上的其他进程...")
    kill_process_on_port(8888)

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta

import crud
import models
import security
import schemas_legacy as schemas
from database import engine, Base
from config import settings
from routers import inspirations, admin_audit_log, models as models_router, dashboard, tasks, images, workflows, prompts, lora_new as lora, base_model, file_system, image_gen_config, config_sync, frontend_config, backup, backup_schedule
from dependencies import get_db, get_current_user

Base.metadata.create_all(bind=engine)

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # 前端开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inspirations.router, prefix="/api")
app.include_router(lora.router, prefix="/api")  # 将LoRA路由移到最前面
app.include_router(admin_audit_log.router, prefix="/api")
app.include_router(models_router.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(base_model.router, prefix="/api")
app.include_router(file_system.router, prefix="/api")
app.include_router(frontend_config.router, prefix="/api/frontend")
app.include_router(image_gen_config.router, prefix="/api/admin")
app.include_router(config_sync.router, prefix="/api/admin/config-sync")
app.include_router(backup.router, prefix="/api/admin")
app.include_router(backup_schedule.router, prefix="/api/admin")

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=schemas.AdminUser)
def create_user(user: schemas.AdminUserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/me/", response_model=schemas.AdminUser)
async def read_users_me(current_user: schemas.AdminUser = Depends(get_current_user)):
    return current_user

@app.get("/")
def read_root():
    return {"Hello": "World", "Hot Reload": "Working!", "Timestamp": "2024-01-01", "Test": "热重载测试成功！"}

if __name__ == "__main__":
    import uvicorn
    import multiprocessing
    
    # 设置Windows多进程启动方法
    if hasattr(multiprocessing, 'set_start_method'):
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            pass  # 如果已经设置过，忽略错误
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        reload_dirs=["./"],
        # Windows特定的配置
        workers=1,  # 单进程模式，避免多进程问题
        loop="asyncio",  # 使用asyncio事件循环
        # 添加进程管理配置
        reload_delay=1.0,  # 文件变化后延迟1秒重载
        reload_excludes=["*.pyc", "*.pyo", "__pycache__"],  # 排除不需要监控的文件
    )