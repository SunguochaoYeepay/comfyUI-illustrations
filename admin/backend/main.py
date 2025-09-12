from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

import crud, models, security
import schemas_legacy as schemas
from database import engine
from config import settings
from routers import inspirations, admin_audit_log, models as models_router, dashboard, tasks, images, workflows, prompts, lora, base_model
from dependencies import get_db, get_current_user

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(inspirations.router, prefix="/api")
app.include_router(admin_audit_log.router, prefix="/api")
app.include_router(models_router.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(lora.router, prefix="/api")
app.include_router(base_model.router)

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
    return {"Hello": "World"}