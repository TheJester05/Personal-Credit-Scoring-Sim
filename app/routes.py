from fastapi import APIRouter
from .models import SimulationRequest, SimulationResult
from .scoring import compute_credit_score
from .db import db
from fastapi import HTTPException

router = APIRouter(prefix="/api/v1")

@router.post("/simulate", response_model=SimulationResult)
async def simulate_credit_score(data: SimulationRequest):
    score_result = compute_credit_score(
    profile=data.profile.dict(),
    actions=data.actions
    )
    

    await db.simulations.insert_one({
        "username": data.username,
        "score": score_result["total"],
        "breakdown": score_result,
        "actions": data.actions
    })

    return {
        "score": score_result["total"],
        "breakdown": score_result
    }

@router.get("/score/{username}", response_model=SimulationResult)
async def get_latest_score(username: str):
    """
    Returns the most recent score and breakdown for a given user.
    """
    latest = await db.simulations.find_one(
        {"username": username},
        sort=[("_id", -1)]
    )

    if not latest:
        raise HTTPException(status_code=404, detail="No score found for this user")

    return {
        "score": latest["score"],
        "breakdown": latest["breakdown"]
    }