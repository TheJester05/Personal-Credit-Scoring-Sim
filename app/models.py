from pydantic import BaseModel, Field
from typing import List, Dict


class FinancialProfile(BaseModel):
    payment_history: float = Field(..., ge=0, le=100, description="Percent of on-time payments (0–100)")
    credit_utilization: float = Field(..., ge=0, le=100, description="Current % of credit used (0–100)")
    length_of_history: float = Field(..., ge=0, le=100, description="Credit history length as normalized (0–100)")
    credit_mix: float = Field(..., ge=0, le=100, description="Diversity of credit types (0–100)")
    inquiries: float = Field(..., ge=0, le=100, description="Inquiries scaled to 0–100")

class SimulationRequest(BaseModel):
    username: str
    profile: FinancialProfile
    actions: List[str] = []

class SimulationResult(BaseModel):
    score: int
    breakdown: Dict[str, int]