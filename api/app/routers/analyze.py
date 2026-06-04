from fastapi import APIRouter

from app.models import AnalyzeRequest, AnalyzeResponse
from app.services.analysis import analyze_symbol

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return analyze_symbol(request.symbol, request.period)
