from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from database import users_collection
from auth import hash_password, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/signup")
def signup(user: UserCreate):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed_pw = hash_password(user.password)
    users_collection.insert_one({"username": user.username, "password": hashed_pw})
    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"message": "Login successful.","access_token": token,"token_type": "bearer"}

@app.post("/logout")
def logout():
    return {"message": "Logout successful."}

@app.get("/")
def read_root():
    return {"message": "testing123backendgup"}

