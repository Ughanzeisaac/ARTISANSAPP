from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status,Request
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import logging

from ..models.client import PyObjectId

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, secret_key: str, algorithm: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt

async def get_current_client(request: Request, token: str = Depends(oauth2_scheme)):
    """Get the current authenticated client from the JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            request.app.settings.SECRET_KEY, 
            algorithms=[request.app.settings.ALGORITHM]
        )
        client_id: str = payload.get("sub")
        if client_id is None:
            raise credentials_exception
    except JWTError as e:
        logging.error(f"JWT error: {e}")
        raise credentials_exception
    
    client = await request.app.mongodb["clients"].find_one({"_id": PyObjectId(client_id)})
    if client is None:
        raise credentials_exception
    return client

async def get_current_artisan(request: Request, token: str = Depends(oauth2_scheme)):
    """Get the current authenticated artisan from the JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            request.app.settings.SECRET_KEY, 
            algorithms=[request.app.settings.ALGORITHM]
        )
        artisan_id: str = payload.get("sub")
        if artisan_id is None:
            raise credentials_exception
    except JWTError as e:
        logging.error(f"JWT error: {e}")
        raise credentials_exception
    
    artisan = await request.app.mongodb["artisans"].find_one({"_id": PyObjectId(artisan_id)})
    if artisan is None:
        raise credentials_exception
    return artisan