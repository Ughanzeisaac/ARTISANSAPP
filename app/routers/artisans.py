from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional, List
from datetime import datetime
import logging

from ..models.artisan import ArtisanInDB
from ..schemas.artisan import ArtisanOut
from ..utils.database import get_db
from ..utils.security import get_current_client

artisans_router = APIRouter()

@artisans_router.get("/search", response_model=List[ArtisanOut])
async def search_artisans(
    request: Request,
    query: Optional[str] = Query(None, min_length=1),
    location: Optional[str] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    available_from: Optional[datetime] = None,
    available_to: Optional[datetime] = None,
    sort_by: Optional[str] = Query("relevance", regex="^(relevance|distance|rating)$"),
    limit: int = Query(10, le=50),
    skip: int = 0
):
    db = request.app.mongodb
    
    search_filter = {}
    
    if query:
        search_filter["$text"] = {"$search": query}
    
    if location:
        search_filter["location"] = {"$regex": location, "$options": "i"}
    
    if min_rating is not None:
        search_filter["rating"] = {"$gte": min_rating}
    
    if available_from and available_to:
        search_filter["availability"] = {
            "$elemMatch": {
                "from": {"$lte": available_from},
                "to": {"$gte": available_to}
            }
        }
    
    sort_criteria = []
    if sort_by == "relevance" and query:
        sort_criteria.append(("score", {"$meta": "textScore"}))
    elif sort_by == "rating":
        sort_criteria.append(("rating", -1))
    elif sort_by == "distance":
        pass
    
    artisans = await db["artisans"].find(
        search_filter,
        {"score": {"$meta": "textScore"}} if query else {}
    ).sort(sort_criteria).skip(skip).limit(limit).to_list(limit)
    
    return [ArtisanOut(**artisan) for artisan in artisans]