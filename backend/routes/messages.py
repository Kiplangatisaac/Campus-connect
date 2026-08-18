from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import Optional
import os
import uuid
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..models.message import Message, Conversation, ConversationParticipant, MessageRead
from ..schemas.message import (
    MessageCreate, MessageResponse, MessageUpdate,
    ConversationCreate, ConversationResponse, ConversationParticipantResponse,
    MessageSearch
)
from ..dependencies import get_current_user
from ..config import settings

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Conversation)
        .join(ConversationParticipant)
        .where(ConversationParticipant.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()

    responses = []
    for conv in conversations:
        participants_stmt = (
            select(ConversationParticipant, User)
            .join(User, ConversationParticipant.user_id == User.id)
            .where(ConversationParticipant.conversation_id == conv.id)
        )
        participants_result = await db.execute(participants_stmt)
        participants_rows = participants_result.all()

        participants = [
            ConversationParticipantResponse(
                id=p.id,
                user_id=u.id,
                username=u.username,
                full_name=u.full_name,
                avatar_url=u.avatar_url,
                is_online=False,
                last_seen=u.last_seen,
                joined_at=p.joined_at,
            )
            for p, u in participants_rows
        ]

        last_message_stmt = (
            select(Message)
            .where(Message.conversation_id == conv.id, Message.is_deleted == False)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_message_result = await db.execute(last_message_stmt)
        last_message = last_message_result.scalar_one_or_none()

        last_message_response = None
        if last_message:
            sender_result = await db.execute(select(User).where(User.id == last_message.sender_id))
            sender = sender_result.scalar_one()
            last_message_response = MessageResponse(
                id=last_message.id,
                content=last_message.content,
                message_type=last_message.message_type,
                media_url=last_message.media_url,
                sender_id=last_message.sender_id,
                sender_name=sender.full_name,
                sender_avatar=sender.avatar_url,
                conversation_id=last_message.conversation_id,
                is_edited=last_message.is_edited,
                is_deleted=last_message.is_deleted,
                created_at=last_message.created_at,
                updated_at=last_message.updated_at,
            )

        unread_stmt = select(func.count(Message.id)).where(
            Message.conversation_id == conv.id,
            Message.sender_id != current_user.id,
            ~Message.id.in_(
                select(MessageRead.message_id).where(MessageRead.user_id == current_user.id)
            )
        )
        unread_count = await db.scalar(unread_stmt) or 0

        responses.append(ConversationResponse(
            id=conv.id,
            name=conv.name,
            type=conv.type,
            group_id=conv.group_id,
            participants=[p.model_dump() for p in participants],
            last_message=last_message_response,
            unread_count=unread_count,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        ))

    return responses


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if len(data.participant_ids) == 1:
        existing_conv_stmt = (
            select(Conversation)
            .join(ConversationParticipant)
            .where(Conversation.type == "direct")
            .where(ConversationParticipant.user_id == current_user.id)
            .where(
                Conversation.id.in_(
                    select(ConversationParticipant.conversation_id)
                    .where(ConversationParticipant.user_id == data.participant_ids[0])
                )
            )
        )
        existing = await db.execute(existing_conv_stmt)
        existing_conv = existing.scalar_one_or_none()

        if existing_conv:
            return await _build_conversation_response(existing_conv.id, current_user.id, db)

    conversation = Conversation(
        name=data.name,
        type="direct" if len(data.participant_ids) == 1 else "group",
    )
    db.add(conversation)
    await db.flush()

    all_participants = [current_user.id] + data.participant_ids
    for user_id in set(all_participants):
        participant = ConversationParticipant(
            conversation_id=conversation.id,
            user_id=user_id,
        )
        db.add(participant)

    await db.flush()
    return await _build_conversation_response(conversation.id, current_user.id, db)


async def _build_conversation_response(conv_id: int, user_id: int, db: AsyncSession) -> ConversationResponse:
    conv = await db.get(Conversation, conv_id)

    participants_stmt = (
        select(ConversationParticipant, User)
        .join(User, ConversationParticipant.user_id == User.id)
        .where(ConversationParticipant.conversation_id == conv_id)
    )
    participants_result = await db.execute(participants_stmt)
    participants_rows = participants_result.all()

    participants = [
        ConversationParticipantResponse(
            id=p.id,
            user_id=u.id,
            username=u.username,
            full_name=u.full_name,
            avatar_url=u.avatar_url,
            is_online=False,
            last_seen=u.last_seen,
            joined_at=p.joined_at,
        )
        for p, u in participants_rows
    ]

    return ConversationResponse(
        id=conv.id,
        name=conv.name,
        type=conv.type,
        group_id=conv.group_id,
        participants=[p.model_dump() for p in participants],
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    participant_check = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
        )
    )
    if not participant_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    return await _build_conversation_response(conversation_id, current_user.id, db)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: int,
    before: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    participant_check = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
        )
    )
    if not participant_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.is_deleted == False)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    if before:
        msg = await db.get(Message, before)
        if msg:
            stmt = stmt.where(Message.created_at < msg.created_at)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    responses = []
    for msg in reversed(messages):
        sender = await db.get(User, msg.sender_id)
        responses.append(MessageResponse(
            id=msg.id,
            content=msg.content,
            message_type=msg.message_type,
            media_url=msg.media_url,
            sender_id=msg.sender_id,
            sender_name=sender.full_name if sender else "Unknown",
            sender_avatar=sender.avatar_url if sender else None,
            conversation_id=msg.conversation_id,
            is_edited=msg.is_edited,
            is_deleted=msg.is_deleted,
            created_at=msg.created_at,
            updated_at=msg.updated_at,
        ))

    return responses


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    participant_check = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == data.conversation_id,
            ConversationParticipant.user_id == current_user.id,
        )
    )
    if not participant_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    message = Message(
        content=data.content,
        message_type=data.message_type,
        media_url=data.media_url,
        sender_id=current_user.id,
        conversation_id=data.conversation_id,
    )
    db.add(message)

    conversation = await db.get(Conversation, data.conversation_id)
    if conversation:
        conversation.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(message)

    return MessageResponse(
        id=message.id,
        content=message.content,
        message_type=message.message_type,
        media_url=message.media_url,
        sender_id=message.sender_id,
        sender_name=current_user.full_name,
        sender_avatar=current_user.avatar_url,
        conversation_id=message.conversation_id,
        is_edited=message.is_edited,
        is_deleted=message.is_deleted,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


@router.put("/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: int,
    data: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    if message.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    message.content = data.content
    message.is_edited = True
    await db.flush()
    await db.refresh(message)

    return MessageResponse(
        id=message.id,
        content=message.content,
        message_type=message.message_type,
        media_url=message.media_url,
        sender_id=message.sender_id,
        sender_name=current_user.full_name,
        sender_avatar=current_user.avatar_url,
        conversation_id=message.conversation_id,
        is_edited=message.is_edited,
        is_deleted=message.is_deleted,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    if message.sender_id != current_user.id and current_user.role.value not in ["admin", "moderator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    message.is_deleted = True
    message.content = None
    await db.flush()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    ALLOWED_UPLOAD_TYPES = {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    }
    if file.content_type and file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type '{file.content_type}' is not allowed")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1] if file.filename else ".bin"
    SAFE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".doc", ".docx", ".txt"}
    if ext.lower() not in SAFE_EXTENSIONS:
        ext = ".bin"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return {"url": f"/uploads/{filename}", "filename": file.filename, "size": len(content)}


@router.post("/search", response_model=list[MessageResponse])
async def search_messages(
    data: MessageSearch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Message).where(Message.is_deleted == False)

    if data.query:
        stmt = stmt.where(Message.content.ilike(f"%{data.query}%"))

    if data.conversation_id:
        stmt = stmt.where(Message.conversation_id == data.conversation_id)

    if data.sender_id:
        stmt = stmt.where(Message.sender_id == data.sender_id)

    if data.start_date:
        stmt = stmt.where(Message.created_at >= data.start_date)

    if data.end_date:
        stmt = stmt.where(Message.created_at <= data.end_date)

    stmt = stmt.order_by(Message.created_at.desc())
    stmt = stmt.offset((data.page - 1) * data.limit).limit(data.limit)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    responses = []
    for msg in messages:
        sender = await db.get(User, msg.sender_id)
        responses.append(MessageResponse(
            id=msg.id,
            content=msg.content,
            message_type=msg.message_type,
            media_url=msg.media_url,
            sender_id=msg.sender_id,
            sender_name=sender.full_name if sender else "Unknown",
            sender_avatar=sender.avatar_url if sender else None,
            conversation_id=msg.conversation_id,
            is_edited=msg.is_edited,
            is_deleted=msg.is_deleted,
            created_at=msg.created_at,
            updated_at=msg.updated_at,
        ))

    return responses
