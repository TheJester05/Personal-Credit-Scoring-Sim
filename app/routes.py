from fastapi import APIRouter
from .models import SimulationRequest, SimulationResult
from .scoring import compute_credit_score
from .db import db
from fastapi import HTTPException
from .models import UserProfile

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
    
@router.post("/profile")
async def save_user_profile(data: UserProfile):
    """
    Save user's general and financial profile.
    Also calculates and stores initial simulated score and breakdown.
    """
    profile_dict = data.profile.dict()
    score_result = compute_credit_score(profile=profile_dict)

    await db.simulations.insert_one({
        "username": data.email,
        "first_name": data.first_name,
        "last_name": data.last_name,
        "age": data.age,
        "employment_status": data.employment_status,
        "financial_profile": profile_dict,
        "score": score_result["total"],
        "breakdown": score_result,
        "actions": []
    })

    return {
        "message": "Profile saved successfully",
        "score": score_result["total"],
        "breakdown": score_result
    }
