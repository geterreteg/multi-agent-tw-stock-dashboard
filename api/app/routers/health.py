from fastapi import APIRouter

from app.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="multi-agent-stock-api", version="0.1.0")
