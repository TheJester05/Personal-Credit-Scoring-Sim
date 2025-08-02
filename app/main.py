from fastapi import FastAPI, Request, Form, Response, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from jose import JWTError, jwt
import datetime
import bcrypt

# ─── Config ───
SECRET_KEY = "RuOGYW2bMF72L-sfhs7IrwD8AwOtWGugcjrpLyPfRg8"
ALGORITHM = "HS256"

# ─── App Setup ───
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ─── MongoDB Setup ───
client = MongoClient("mongodb://localhost:27017")
db = client["credit_sim_db"]
users = db["users"]
auth_users = db["auth_users"]
simulations = db["simulations"]
scores = db["score"]

# ─── Helpers ───
def calculate_score(profile):
    return round((
        profile.get("payment_history", 0) * 0.35 +
        profile.get("credit_utilization", 0) * 0.30 +
        profile.get("length_of_history", 0) * 0.15 +
        profile.get("credit_mix", 0) * 0.10 +
        profile.get("inquiries", 0) * 0.10
    ) * 8.5 + 300, 2)

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return email

# ─── Pages ───
@app.get("/", response_class=HTMLResponse)
@app.get("/index", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
@app.get("/login.html", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
@app.get("/signup.html", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

@app.get("/profile", response_class=HTMLResponse)
@app.get("/profile.html", response_class=HTMLResponse)
def profile_page(request: Request, email: str = Depends(get_current_user)):
    user = users.find_one({"email": email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@app.post("/submit-profile")
def submit_profile(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    age: int = Form(...),
    employment_status: str = Form(...),
    income: str = Form(...),
    credit_limit: str = Form(...),
    current_debt: str = Form(...),
    late_payments: str = Form(...),
    loan_history: str = Form(...),
    utilization: int = Form(...),
):
    try:
        credit_limit_val = float(credit_limit)
        current_debt_val = float(current_debt)
        late_payments_val = int(late_payments)
        utilization_val = int(utilization)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid numerical input")

    profile = {
        "payment_history": max(0, 100 - late_payments_val * 10),
        "credit_utilization": max(0, 100 - utilization_val),
        "length_of_history": max(0, min(10, int(age) - 18) * 10),
        "credit_mix": 70 if loan_history.lower() == "good" else 40,
        "inquiries": max(0, 100 - (current_debt_val / max(credit_limit_val, 1)) * 100)
    }

    score = calculate_score(profile)

    users.update_one({"email": email}, {
        "$set": {
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
            "profile": profile,
            "score": score,
            "breakdown": profile
        }
    }, upsert=True)

    simulations.delete_many({"email": email})
    scores.delete_many({"email": email})

    return RedirectResponse(url="/simulator", status_code=302)

@app.get("/simulator", response_class=HTMLResponse)
@app.get("/simulator.html", response_class=HTMLResponse)
def simulator_page(request: Request, email: str = Depends(get_current_user)):
    user = users.find_one({"email": email})
    if not user:
        return HTMLResponse("User not found", status_code=404)

    profile = user.get("profile", {})
    score = calculate_score(profile)
    users.update_one({"email": email}, {"$set": {"score": score, "profile": profile}})

    return templates.TemplateResponse("simulator.html", {
        "request": request,
        "sim_data": {
            "email": email,
            "score": score,
            "profile": profile
        }
    })

@app.get("/score", response_class=HTMLResponse)
@app.get("/score.html", response_class=HTMLResponse)
def score_page(request: Request, email: str = Depends(get_current_user)):
    user = users.find_one({"email": email})
    if not user:
        return HTMLResponse("User not found", status_code=404)

    profile = user.get("profile", {})
    score = calculate_score(profile)
    users.update_one({"email": email}, {"$set": {"score": score, "profile": profile}})

    scores.insert_one({
        "email": email,
        "score": score,
        "breakdown": profile,
        "timestamp": datetime.datetime.utcnow()
    })

    return templates.TemplateResponse("score.html", {
        "request": request,
        "email": email,
        "score": score,
        "breakdown": profile,
        "sim_data": {
            "email": email,
            "score": score,
            "breakdown": profile
        }
    })

@app.get("/get-profile/{email}")
def get_profile(email: str):
    user = users.find_one({"email": email}, {"_id": 0})
    if not user:
        return {"error": "User not found"}
    return {k: v for k, v in user.items() if v not in ["", 0, None]}

@app.post("/signup")
def handle_signup(email: str = Form(...), password: str = Form(...)):
    if auth_users.find_one({"email": email}):
        return HTMLResponse("User already exists", status_code=400)

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    auth_users.insert_one({"email": email, "password": hashed_pw})
    users.insert_one({"email": email})
    return RedirectResponse(url="/login", status_code=302)

@app.post("/login")
async def handle_login(response: Response, email: str = Form(...), password: str = Form(...)):
    user = auth_users.find_one({"email": email})
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode("utf-8")):
        return HTMLResponse("Invalid email or password", status_code=401)

    token = jwt.encode({"sub": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, SECRET_KEY, algorithm=ALGORITHM)
    res = RedirectResponse(url="/profile", status_code=302)
    res.set_cookie(key="access_token", value=token, httponly=True)
    return res

@app.post("/api/v1/simulate")
async def simulate_action(data: dict):
    email = data.get("username")
    actions = data.get("actions", [])

    user = users.find_one({"email": email})
    if not user:
        return {"error": "User not found"}

    profile = user.get("profile", {})
    score_before = calculate_score(profile)

    for action in actions:
        if action == "payOnTime":
            profile["payment_history"] = min(100, profile.get("payment_history", 0) + 5)
        elif action == "missPayment":
            profile["payment_history"] = max(0, profile.get("payment_history", 0) - 20)
        elif action == "openNewCard":
            profile["credit_mix"] = min(100, profile.get("credit_mix", 0) + 5)
        elif action == "closeOldAccount":
            profile["length_of_history"] = max(0, profile.get("length_of_history", 0) - 10)
        elif action == "reduceUtilization":
            profile["credit_utilization"] = min(100, profile.get("credit_utilization", 0) + 10)

    score_after = calculate_score(profile)
    users.update_one({"email": email}, {"$set": {"profile": profile, "score": score_after}})

    simulations.insert_one({
        "email": email,
        "actions": actions,
        "score_before": score_before,
        "score_after": score_after,
        "profile": profile,
        "timestamp": datetime.datetime.utcnow()
    })

    return {"score": score_after, "updated_profile": profile}

@app.get("/tips", response_class=HTMLResponse)
@app.get("/tips.html", response_class=HTMLResponse)
def tips_page(request: Request, email: str = Depends(get_current_user)):
    return templates.TemplateResponse("tips.html", {"request": request})

@app.get("/tip1.html", response_class=HTMLResponse)
@app.get("/tip2.html", response_class=HTMLResponse)
@app.get("/tip3.html", response_class=HTMLResponse)
@app.get("/tip4.html", response_class=HTMLResponse)
@app.get("/tip5.html", response_class=HTMLResponse)
@app.get("/tip6.html", response_class=HTMLResponse)
def tip_page(request: Request):
    return templates.TemplateResponse("tip1.html", {"request": request})