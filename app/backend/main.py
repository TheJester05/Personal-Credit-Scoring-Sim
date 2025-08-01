from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from routes import router

# ─── FastAPI & Middleware Setup ─────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static & Template Setup ───────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(router)

# ─── MongoDB Setup ─────────────────────────────────────────
client = MongoClient("mongodb://localhost:27017")
db = client["credit_db"]
users = db["users"]

# ─── Scoring Logic ─────────────────────────────────────────
def calculate_score(profile):
    score = (
        profile.get("payment_history", 0) * 0.35 +
        profile.get("credit_utilization", 0) * 0.30 +
        profile.get("length_of_history", 0) * 0.15 +
        profile.get("credit_mix", 0) * 0.10 +
        profile.get("inquiries", 0) * 0.10
    ) * 100
    return round(score, 2)

# ─── HTML Routes ───────────────────────────────────────────

@app.get("/profile", response_class=HTMLResponse)
def show_profile_form(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.post("/profile")
def save_profile(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    age: int = Form(...),
    employment_status: str = Form(...),
    payment_history: float = Form(...),
    credit_utilization: float = Form(...),
    length_of_history: float = Form(...),
    credit_mix: float = Form(...),
    inquiries: float = Form(...)
):
    profile_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "age": age,
        "employment_status": employment_status,
        "profile": {
            "payment_history": payment_history,
            "credit_utilization": credit_utilization,
            "length_of_history": length_of_history,
            "credit_mix": credit_mix,
            "inquiries": inquiries,
        }
    }
    users.update_one({"email": email}, {"$set": profile_data}, upsert=True)
    return RedirectResponse(url=f"/simulator?email={email}", status_code=302)

@app.get("/simulator", response_class=HTMLResponse)
def show_simulator(request: Request, email: str = Query(...)):
    user = users.find_one({"email": email})
    if not user:
        return HTMLResponse("User not found", status_code=404)

    score = calculate_score(user["profile"])
    return templates.TemplateResponse("simulator.html", {
        "request": request,
        "email": email,
        "score": score
    })

@app.get("/score", response_class=HTMLResponse)
def show_score_breakdown(request: Request, email: str = Query(...)):
    user = users.find_one({"email": email})
    if not user:
        return HTMLResponse("User not found", status_code=404)

    profile = user["profile"]
    score = calculate_score(profile)
    return templates.TemplateResponse("score.html", {
        "request": request,
        "email": email,
        "score": score,
        "profile": profile
    })