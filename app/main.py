from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings


app = FastAPI()


from routers.artisans import artisans_router
from routers.bookings import bookings_router
from routers.clients import clients_router
from routers.reviews import reviews_router
from routers.payments import payments_router
from routers.messages import messages_router



app.include_router(clients_router, prefix="/api/clients")
app.include_router(artisans_router, prefix="/api/artisans")
app.include_router(bookings_router, prefix="/api/bookings")
app.include_router(reviews_router, prefix="/api/reviews")
app.include_router(payments_router, prefix="/api/payments")
app.include_router(messages_router, prefix="/api/messages")






class Settings(BaseSettings): 
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_NAME: str = "artisan_booking"
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SMTP_SERVER: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "your-email@example.com"
    SMTP_PASSWORD: str = "your-email-password"
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def root():
    return {"message": "Welcome to Artisan Booking System"}