from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .db import ping_db,close_db
from .api import users,jobs,matching,agent,resumes,applications,health

settings=get_settings()

@asynccontextmanager
async def lifespan(app):
    await ping_db()
    yield
    await close_db()

app=FastAPI(title=settings.app_name,version="1.0.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(health.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(matching.router)
app.include_router(agent.router)
app.include_router(resumes.router)
app.include_router(applications.router)
