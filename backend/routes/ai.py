from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..limiter import limiter
import os
import httpx

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = "general"

class ChatResponse(BaseModel):
    response: str
    suggestions: list[str] = []
    confidence: float = 0.0

UNIVERSITY_INFO = """
You are KyU Campus Connect AI Assistant for Kirinyaga University.
You help students with:
- Campus navigation and locations
- Course information and academic calendar
- Student services and resources
- Chat features and app usage
- University policies and procedures
- Finding study groups and campus events
- Technical support for the app

Kirinyaga University Motto: "Innovative Technology for a Dynamic World"
ISO 9001:2015 Certified

Always be helpful, friendly, and concise. Use emojis appropriately.
"""

AI_RESPONSES = {
    "greeting": [
        "Hello! I'm KyU Assistant. How can I help you today?",
        "Hi there! Welcome to KyU Campus Connect. What can I do for you?",
        "Hey! I'm here to help with anything campus-related. What's up?"
    ],
    "help": [
        "I can help you with:\n- Finding campus locations\n- Academic information\n- Student services\n- App features\n- Study groups\n\nJust ask me anything!",
    ],
    "locations": [
        "Our main campus is in Kerugoya, Kirinyaga County. Key locations include:\n- Main Administration Block\n- Library Complex\n- Student Center\n- Lecture Halls A-D\n- Sports Complex\n- Cafeteria\n\nNeed directions to a specific place?"
    ],
    "services": [
        "Student services available:\n- Academic Affairs\n- Student Welfare\n- Career Services\n- Health Center\n- Counseling\n- IT Support\n\nWhich service do you need help with?"
    ],
    "chat": [
        "Chat features available:\n- Direct messages with classmates\n- Group chats for courses/clubs\n- Voice and video calls\n- File sharing\n- Read receipts\n- Stickers and emojis\n\nWant to learn how to use any of these?"
    ],
    "events": [
        "Check the Events section for:\n- Academic deadlines\n- Club meetings\n- Sports events\n- Workshops\n- Campus parties\n\nWould you like me to help you find specific events?"
    ],
    "study": [
        "Study groups are a great way to learn! You can:\n- Join existing groups in Groups tab\n- Create a new study group\n- Share notes and resources\n- Schedule study sessions\n\nNeed help finding study partners?"
    ],
    "default": [
        "I'm here to help! Could you tell me more about what you need?",
        "Interesting question! Let me help you with that.",
        "I'd be happy to assist. Can you provide more details?"
    ]
}

def get_response_category(message: str) -> str:
    message = message.lower()
    if any(word in message for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return "greeting"
    elif any(word in message for word in ["help", "what can you do", "features"]):
        return "help"
    elif any(word in message for word in ["location", "where", "campus", "direction", "block", "building"]):
        return "locations"
    elif any(word in message for word in ["service", "support", "welfare", "health", "counseling", "career"]):
        return "services"
    elif any(word in message for word in ["chat", "message", "call", "video", "voice", "send"]):
        return "chat"
    elif any(word in message for word in ["event", "meeting", "deadline", "calendar", "party"]):
        return "events"
    elif any(word in message for word in ["study", "group", "notes", "learn", "class", "course"]):
        return "study"
    else:
        return "default"

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_with_ai(
    request: Request,
    msg: ChatMessage,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    category = get_response_category(msg.message)
    import random
    response = random.choice(AI_RESPONSES[category])
    
    suggestions = []
    if category == "greeting":
        suggestions = ["Find study groups", "View events", "Get campus info"]
    elif category == "help":
        suggestions = ["Campus locations", "Student services", "Chat features"]
    elif category == "locations":
        suggestions = ["Get directions", "View campus map", "Find facilities"]
    
    return ChatResponse(
        response=response,
        suggestions=suggestions,
        confidence=0.95
    )

@router.get("/suggestions")
@limiter.limit("30/minute")
async def get_suggestions(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return {
        "suggestions": [
            "What services are available?",
            "How do I join a study group?",
            "Where is the library?",
            "What events are happening?",
            "How do I use video calls?",
            "Find me study partners"
        ]
    }
