from fastapi import APIRouter, Request

from app.config import APP_VERSION

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict:
    active = request.app.state.container.registry.active()
    return {"status": "ok", "version": APP_VERSION, "active_model": active["version"] if active else None}
