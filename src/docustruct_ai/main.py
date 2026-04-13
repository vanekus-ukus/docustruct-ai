from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from docustruct_ai.api.routes.documents import router as documents_router
from docustruct_ai.api.routes.evaluation import router as evaluation_router
from docustruct_ai.api.routes.health import router as health_router
from docustruct_ai.api.routes.review import router as review_router
from docustruct_ai.config import get_settings
from docustruct_ai.db.base import Base
from docustruct_ai.db.session import engine
from docustruct_ai.logging import configure_logging
from docustruct_ai.models import all_models  # noqa: F401

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="docustruct-ai",
    description="Гибридная платформа для структурного извлечения данных из документов.",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(health_router)
app.include_router(documents_router)
app.include_router(review_router)
app.include_router(evaluation_router)
