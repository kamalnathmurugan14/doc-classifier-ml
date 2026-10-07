from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import categories, datasets, fs, health, labels, models, predict, training
from app.config import APP_VERSION, Settings, get_settings
from app.deps import Container
from app.errors import install_error_handlers
from app.logging_conf import setup_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    setup_logging()
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = Container(settings)
        yield

    app = FastAPI(title="Document Classifier ML", version=APP_VERSION, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.origins, allow_methods=["GET", "POST", "DELETE"], allow_headers=["*"]
    )
    install_error_handlers(app)
    for r in (health, fs, categories, labels, training, models, predict, datasets):
        app.include_router(r.router)
    return app


app = create_app()
