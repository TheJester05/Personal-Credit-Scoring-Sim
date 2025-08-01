from fastapi import APIRouter, HTTPException
from .models import SimulationRequest, SimulationResult, UserProfile
from .scoring import compute_credit_score
from .db import db

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

@router.get("/profile/{email}")
async def get_user_profile(email: str):
    profile = await db.simulations.find_one(
        {"username": email},
        sort=[("_id", -1)]
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "first_name": profile.get("first_name"),
        "last_name": profile.get("last_name"),
        "age": profile.get("age"),
        "employment_status": profile.get("employment_status"),
        "financial_profile": profile.get("financial_profile"),
        "score": profile.get("score"),
        "breakdown": profile.get("breakdown")
    }
