from fastapi import APIRouter, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from datetime import datetime
from typing import List, Optional
import logging
from bson import ObjectId

from ..models.messages import MessageInDB, PyObjectId
from ..schemas.messages import MessageOut, MessageCreate, Conversation
from ..utils.database import get_db
from ..utils.security import get_current_client, get_current_artisan
from ..utils.websocket import ConnectionManager

messages_router = APIRouter()


manager = ConnectionManager()

@messages_router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    token: str
):
    """WebSocket endpoint for real-time messaging"""
    try:
        
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        
        connection_id = f"{client_id}_{datetime.now().timestamp()}"

        await manager.connect(websocket, client_id, connection_id)
        
        try:
            while True:
                data = await websocket.receive_json()
                await manager.send_personal_message(
                    {"message": "Received your message", "your_data": data},
                    client_id
                )
        except WebSocketDisconnect:
            manager.disconnect(connection_id)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

@messages_router.post("/", response_model=MessageOut)
async def create_message(
    message: MessageCreate,
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    """Create a new message"""
    db = request.app.mongodb
    
    
    recipient = await db["clients"].find_one({"_id": message.recipient_id}) or \
                await db["artisans"].find_one({"_id": message.recipient_id})
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

   
    message_db = MessageInDB(
        **message.dict(),
        sender_id=current_client["_id"],
        read=False
    )

    # Save to database
    inserted_message = await db["messages"].insert_one(message_db.dict(by_alias=True))
    created_message = await db["messages"].find_one({"_id": inserted_message.inserted_id})

    
    await manager.send_personal_message({
        "type": "new_message",
        "message_id": str(created_message["_id"]),
        "sender_id": str(created_message["sender_id"]),
        "content": created_message["content"],
        "timestamp": created_message["created_at"].isoformat()
    }, str(message.recipient_id))

    return MessageOut(**created_message)

@messages_router.get("/", response_model=List[MessageOut])
async def get_messages(
    request: Request,
    recipient_id: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_client: dict = Depends(get_current_client)
):
    """Get messages for current user, optionally filtered by recipient"""
    db = request.app.mongodb
    
    query = {
        "$or": [
            {"sender_id": current_client["_id"]},
            {"recipient_id": current_client["_id"]}
        ]
    }
    
    if recipient_id:
        query["$or"] = [
            {
                "sender_id": current_client["_id"],
                "recipient_id": PyObjectId(recipient_id)
            },
            {
                "sender_id": PyObjectId(recipient_id),
                "recipient_id": current_client["_id"]
            }
        ]

    messages = await db["messages"].find(query) \
        .sort("created_at", -1) \
        .skip(skip) \
        .limit(limit) \
        .to_list(limit)
    
    return [MessageOut(**msg) for msg in messages]

@messages_router.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    """Get all conversations for current user"""
    db = request.app.mongodb
    
    # Get distinct participants
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"sender_id": current_client["_id"]},
                    {"recipient_id": current_client["_id"]}
                ]
            }
        },
        {
            "$project": {
                "participant": {
                    "$cond": {
                        "if": {"$eq": ["$sender_id", current_client["_id"]]},
                        "then": "$recipient_id",
                        "else": "$sender_id"
                    }
                },
                "last_message": "$$ROOT",
                "read": "$read"
            }
        },
        {
            "$sort": {"last_message.created_at": -1}
        },
        {
            "$group": {
                "_id": "$participant",
                "last_message": {"$first": "$last_message"},
                "unread_count": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$last_message.recipient_id", current_client["_id"]]},
                                {"$eq": ["$read", False]}
                            ]},
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$lookup": {
                "from": "clients",
                "localField": "_id",
                "foreignField": "_id",
                "as": "client"
            }
        },
        {
            "$lookup": {
                "from": "artisans",
                "localField": "_id",
                "foreignField": "_id",
                "as": "artisan"
            }
        },
        {
            "$project": {
                "participant": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$client"}, 0]},
                        "then": {"$arrayElemAt": ["$client", 0]},
                        "else": {"$arrayElemAt": ["$artisan", 0]}
                    }
                },
                "last_message": 1,
                "unread_count": 1
            }
        }
    ]

    conversations = await db["messages"].aggregate(pipeline).to_list(1000)
    
    return [Conversation(
        participant=conv["participant"],
        last_message=conv["last_message"],
        unread_count=conv["unread_count"]
    ) for conv in conversations]

@messages_router.put("/{message_id}/read")
async def mark_as_read(
    message_id: str,
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    """Mark a message as read"""
    db = request.app.mongodb
    
    result = await db["messages"].update_one(
        {
            "_id": PyObjectId(message_id),
            "recipient_id": current_client["_id"]
        },
        {"$set": {"read": True, "updated_at": datetime.now()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or not yours to mark as read"
        )
    
    return {"message": "Message marked as read"}

@messages_router.post("/{message_id}/report")
async def report_message(
    message_id: str,
    request: Request,
    reason: str,
    current_client: dict = Depends(get_current_client)
):
    """Report an inappropriate message"""
    db = request.app.mongodb
    
    # Verify message exists and was sent to current user
    message = await db["messages"].find_one({
        "_id": PyObjectId(message_id),
        "$or": [
            {"sender_id": current_client["_id"]},
            {"recipient_id": current_client["_id"]}
        ]
    })
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
   
    report = {
        "message_id": PyObjectId(message_id),
        "reporter_id": current_client["_id"],
        "sender_id": message["sender_id"],
        "recipient_id": message["recipient_id"],
        "reason": reason,
        "created_at": datetime.now(),
        "status": "pending"
    }
    
    await db["reports"].insert_one(report)
    
    return {"message": "Message reported successfully"}