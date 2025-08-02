from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from app.auth_routes import router as auth_router
from app.db import users_collection as users



# ─── FastAPI & Middleware Setup ─────────────────────────────
app = FastAPI()
app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static & Template Setup ───────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ─── MongoDB Setup ─────────────────────────────────────────
client = MongoClient("mongodb://localhost:27017")
db = client["credit_sim_db"]
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

@app.post("/submit-profile")
async def submit_profile(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    age: int = Form(...),
    employment_status: str = Form(...),
    income: str = Form(...),
    credit_limit: str = Form(...),
    current_debt: str = Form(...),
    late_payments: str = Form(...),
    loan_history: str = Form(...),
    utilization: int = Form(...),
):
    
    print({
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "age": age,
        "employment_status": employment_status,
        "income": income,
        "credit_limit": credit_limit,
        "current_debt": current_debt,
        "late_payments": late_payments,
        "loan_history": loan_history,
        "utilization": utilization,
    })

    
    return RedirectResponse(url="/profile", status_code=302)

@app.get("/get-profile/{email}")
async def get_profile(email: str):
    # Fetch from DB here
    dummy_data = {
        "first_name": "Peepar",
        "last_name": "Example",
        "email": email,
        "age": 20,
        "employment_status": "Student",
        "income": "10000",
        "credit_limit": "50000",
        "current_debt": "2000",
        "late_payments": "1",
        "loan_history": "Good",
        "utilization": 40
    }


@app.get("/simulator", response_class=HTMLResponse)
def show_simulator(request: Request, email: str = Query(None)):
    if not email:
        return RedirectResponse(url="/login", status_code=302)

    user = users.find_one({"email": email})
    if not user:
        return HTMLResponse("User not found", status_code=404)

    score = calculate_score(user["profile"])
    return templates.TemplateResponse("simulator.html", {
        "request": request,
        "email": email,
        "score": score
    })

@app.get("/simulator.html", response_class=HTMLResponse)
def simulator_html_redirect(request: Request, email: str = Query(None)):
    return show_simulator(request, email)


from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

@app.get("/score", response_class=HTMLResponse)
def show_score_breakdown(request: Request, email: str):
    return templates.TemplateResponse("score.html", {"request": request, "email": email})

@app.get("/api/v1/score/{email}")
def get_score_breakdown(email: str):
    user = users.find_one({"email": email})
    if user:
        return {
            "email": user["email"],
            "score": user["score"],
            "breakdown": user["breakdown"]
        }
    return {"error": "User not found"}


@app.get("/", response_class=HTMLResponse)
@app.get("/index", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login.html", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def handle_login(email: str = Form(...), password: str = Form(...)):
    user = users.find_one({"email": email})
    
    if not user or user.get("password") != password:
        return HTMLResponse("Invalid login", status_code=401)

    return RedirectResponse(url=f"/simulator?email={email}", status_code=302)



@app.get("/signup.html", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def handle_signup(email: str = Form(...), password: str = Form(...)):
    print(f"Received signup for: {email}")  # ✅ Add this

    if users.find_one({"email": email}):
        return HTMLResponse("User already exists", status_code=400)

    users.insert_one({"email": email, "password": password})
    return RedirectResponse(url="/login", status_code=302)


@app.get("/profile.html", response_class=HTMLResponse)
def get_profile_html(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/tips.html", response_class=HTMLResponse)
def tips_page(request: Request):
    return templates.TemplateResponse("tips.html", {"request": request})

@app.get("/tips", response_class=HTMLResponse)
def tips_alias(request: Request):
    return templates.TemplateResponse("tips.html", {"request": request})

@app.get("/tip1.html", response_class=HTMLResponse)
def tip1_page(request: Request):
    return templates.TemplateResponse("tip1.html", {"request": request})

@app.get("/tip2.html", response_class=HTMLResponse)
def tip1_page(request: Request):
    return templates.TemplateResponse("tip1.html", {"request": request})

@app.get("/tip3.html", response_class=HTMLResponse)
def tip1_page(request: Request):
    return templates.TemplateResponse("tip1.html", {"request": request})

@app.get("/tip4.html", response_class=HTMLResponse)
def tip1_page(request: Request):
    return templates.TemplateResponse("tip1.html", {"request": request})

@app.get("/tip5.html", response_class=HTMLResponse)
def tip1_page(request: Request):
    return templates.TemplateResponse("tip1.html", {"request": request})

@app.get("/tip6.html", response_class=HTMLResponse)
def tip1_page(request: Request):
    return templates.TemplateResponse("tip1.html", {"request": request})