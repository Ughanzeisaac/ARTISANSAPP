from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import logging
from typing import Optional

from ..models.client import ClientInDB
from ..schemas.client import ClientCreate, ClientOut, ClientUpdate, ClientDashboard
from ..utils.database import get_db
from ..utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_client
)
from ..utils.email import send_registration_email, send_password_reset_email

clients_router = APIRouter(prefix="/clients", tags=["clients"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@clients_router.post("/register", response_model=ClientOut)
async def register_client(client: ClientCreate, request: Request):
    db = request.app.mongodb
    
    
    existing_client = await db["clients"].find_one({"email": client.email})
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    
    hashed_password = get_password_hash(client.password)
    
    
    client_db = ClientInDB(
        **client.model_dump(exclude={"password"}),
        hashed_password=hashed_password
    )
    
    inserted_client = await db["clients"].insert_one(client_db.model_dump(by_alias=True))
    created_client = await db["clients"].find_one({"_id": inserted_client.inserted_id})
    
    
    await send_registration_email(
        client.email,
        client.name,
        request.app.settings.FRONTEND_URL,
        request.app.settings
    )
    
    return ClientOut(**created_client)

@clients_router.post("/login")
async def login_client(
    request: Request,  
    form_data: OAuth2PasswordRequestForm = Depends() 
):
    db = request.app.mongodb
    
    client = await db["clients"].find_one({"email": form_data.username})
    if not client or not verify_password(form_data.password, client["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": str(client["_id"])},
        secret_key=request.app.settings.SECRET_KEY,
        algorithm=request.app.settings.ALGORITHM,
        expires_delta=timedelta(minutes=request.app.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "client_id": str(client["_id"])
    }

@clients_router.get("/dashboard", response_model=ClientDashboard)
async def get_client_dashboard(
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    client_id = current_client["_id"]
    
    
    upcoming_bookings = await db["bookings"].find({
        "client_id": client_id,
        "status": {"$in": ["pending", "accepted"]},
        "date": {"$gte": datetime.utcnow()}
    }).sort("date", 1).to_list(5)
    
    
    past_bookings = await db["bookings"].find({
        "client_id": client_id,
        "status": "completed",
        "date": {"$lt": datetime.utcnow()}
    }).sort("date", -1).to_list(5)
    
    return ClientDashboard(
        upcoming_bookings=upcoming_bookings,
        past_bookings=past_bookings
    )

@clients_router.get("/profile", response_model=ClientOut)
async def get_client_profile(
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    return current_client

@clients_router.put("/profile", response_model=ClientOut)
async def update_client_profile(
    client_update: ClientUpdate,
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    client_id = current_client["_id"]
    
    update_data = client_update.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db["clients"].update_one(
        {"_id": client_id},
        {"$set": update_data}
    )
    
    updated_client = await db["clients"].find_one({"_id": client_id})
    return ClientOut(**updated_client)