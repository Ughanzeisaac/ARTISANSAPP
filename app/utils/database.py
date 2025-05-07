from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging
from typing import Optional

async def get_db_client(mongodb_url: str) -> AsyncIOMotorClient:
    """Create and return a MongoDB client connection"""
    try:
        client = AsyncIOMotorClient(mongodb_url)
        await client.admin.command('ping')
        logging.info("Successfully connected to MongoDB")
        return client
    except ConnectionFailure as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_db_client(client: AsyncIOMotorClient):
    """Close the MongoDB client connection"""
    try:
        client.close()
        logging.info("MongoDB connection closed")
    except Exception as e:
        logging.error(f"Error closing MongoDB connection: {e}")
        raise

async def get_db(client: AsyncIOMotorClient, db_name: str):
    """Get a database instance from the client"""
    return client[db_name]

async def create_indexes(db):
    """Create necessary indexes for optimal query performance"""
    # Client indexes
    await db.clients.create_index("email", unique=True)
    
    # Artisan indexes
    await db.artisans.create_index("email", unique=True)
    await db.artisans.create_index([("location", "text"), ("profession", "text"), ("skills", "text")])
    
    # Booking indexes
    await db.bookings.create_index("client_id")
    await db.bookings.create_index("artisan_id")
    await db.bookings.create_index([("status", 1), ("date", 1)])
    
    # Review indexes
    await db.reviews.create_index("artisan_id")
    await db.reviews.create_index("booking_id", unique=True)
    
    # Payment indexes
    await db.payments.create_index("client_id")
    await db.payments.create_index("artisan_id")
    await db.payments.create_index("booking_id")
    
    # Message indexes
    await db.messages.create_index([("sender_id", 1), ("recipient_id", 1)])
    
    logging.info("Database indexes created successfully")