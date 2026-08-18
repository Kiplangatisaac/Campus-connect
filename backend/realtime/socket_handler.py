import socketio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from typing import Optional

from ..config import settings
from ..database import async_session_factory
from ..models.user import User
from ..models.message import Message, Conversation, ConversationParticipant, MessageRead
from ..auth import decode_access_token

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.ALLOWED_ORIGINS,
    logger=settings.DEBUG,
    engineio_logger=settings.DEBUG,
)

online_users: dict[int, str] = {}
user_sids: dict[str, int] = {}


@sio.event
async def connect(sid, environ, auth):
    try:
        token = auth.get("token") if auth else None
        if not token:
            raise ValueError("No token provided")

        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))

        async with async_session_factory() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                raise ValueError("User not found or inactive")

            user.last_seen = datetime.utcnow()
            await db.commit()

        online_users[user_id] = sid
        user_sids[sid] = user_id

        await sio.emit("user_online", {"user_id": user_id}, skip.sid)

        await sio.emit("connected", {
            "user_id": user_id,
            "message": "Connected successfully"
        }, room=sid)

        print(f"User {user_id} connected with SID {sid}")

    except Exception as e:
        print(f"Connection error: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)
        raise socketio.exceptions.ConnectionRefusedError("Authentication failed")


@sio.event
async def disconnect(sid):
    user_id = user_sids.pop(sid, None)
    if user_id:
        online_users.pop(user_id, None)

        try:
            async with async_session_factory() as db:
                await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(last_seen=datetime.utcnow())
                )
                await db.commit()
        except Exception as e:
            print(f"Error updating last_seen: {e}")

        await sio.emit("user_offline", {"user_id": user_id, "last_seen": datetime.utcnow().isoformat()})
        print(f"User {user_id} disconnected")


@sio.event
async def join_conversation(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    conversation_id = data.get("conversation_id")
    if not conversation_id:
        await sio.emit("error", {"message": "conversation_id required"}, room=sid)
        return

    async with async_session_factory() as db:
        participant_check = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
        )
        if not participant_check.scalar_one_or_none():
            await sio.emit("error", {"message": "Not a participant"}, room=sid)
            return

    room_name = f"conversation_{conversation_id}"
    await sio.enter_room(sid, room_name)
    await sio.emit("user_joined_conversation", {
        "user_id": user_id,
        "conversation_id": conversation_id,
    }, room=room_name, skip_sid=sid)


@sio.event
async def leave_conversation(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return

    room_name = f"conversation_{conversation_id}"
    await sio.leave_room(sid, room_name)
    await sio.emit("user_left_conversation", {
        "user_id": user_id,
        "conversation_id": conversation_id,
    }, room=room_name)


@sio.event
async def send_message(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        await sio.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    conversation_id = data.get("conversation_id")
    content = data.get("content")
    message_type = data.get("message_type", "text")
    media_url = data.get("media_url")

    if not conversation_id or not content:
        await sio.emit("error", {"message": "conversation_id and content required"}, room=sid)
        return

    try:
        async with async_session_factory() as db:
            participant_check = await db.execute(
                select(ConversationParticipant).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
            if not participant_check.scalar_one_or_none():
                await sio.emit("error", {"message": "Not a participant"}, room=sid)
                return

            message = Message(
                content=content,
                message_type=message_type,
                media_url=media_url,
                sender_id=user_id,
                conversation_id=conversation_id,
            )
            db.add(message)

            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(updated_at=datetime.utcnow())
            )

            await db.commit()
            await db.refresh(message)

            sender_result = await db.execute(select(User).where(User.id == user_id))
            sender = sender_result.scalar_one()

            message_data = {
                "id": message.id,
                "content": message.content,
                "message_type": message.message_type,
                "media_url": message.media_url,
                "sender_id": message.sender_id,
                "sender_name": sender.full_name,
                "sender_avatar": sender.avatar_url,
                "conversation_id": message.conversation_id,
                "is_edited": message.is_edited,
                "created_at": message.created_at.isoformat() if message.created_at else None,
            }

            room_name = f"conversation_{conversation_id}"
            await sio.emit("new_message", message_data, room=room_name)

    except Exception as e:
        print(f"Error sending message: {e}")
        await sio.emit("error", {"message": "Failed to send message"}, room=sid)


@sio.event
async def typing_start(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return

    room_name = f"conversation_{conversation_id}"
    await sio.emit("user_typing", {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "is_typing": True,
    }, room=room_name, skip_sid=sid)


@sio.event
async def typing_stop(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return

    room_name = f"conversation_{conversation_id}"
    await sio.emit("user_typing", {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "is_typing": False,
    }, room=room_name, skip_sid=sid)


@sio.event
async def mark_read(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    message_id = data.get("message_id")
    conversation_id = data.get("conversation_id")

    if not message_id:
        return

    try:
        async with async_session_factory() as db:
            existing = await db.execute(
                select(MessageRead).where(
                    MessageRead.message_id == message_id,
                    MessageRead.user_id == user_id,
                )
            )
            if not existing.scalar_one_or_none():
                read_receipt = MessageRead(
                    message_id=message_id,
                    user_id=user_id,
                )
                db.add(read_receipt)
                await db.commit()

            if conversation_id:
                room_name = f"conversation_{conversation_id}"
                await sio.emit("message_read", {
                    "message_id": message_id,
                    "user_id": user_id,
                    "read_at": datetime.utcnow().isoformat(),
                }, room=room_name)

    except Exception as e:
        print(f"Error marking read: {e}")


@sio.event
async def get_online_users(sid):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    await sio.emit("online_users", {
        "online_user_ids": list(online_users.keys())
    }, room=sid)


@sio.event
async def send_notification(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    target_user_id = data.get("user_id")
    if not target_user_id:
        return

    notification_data = {
        "from_user_id": user_id,
        "type": data.get("type", "general"),
        "title": data.get("title", ""),
        "message": data.get("message", ""),
        "data": data.get("data", {}),
    }

    if target_user_id in online_users:
        target_sid = online_users[target_user_id]
        await sio.emit("notification", notification_data, room=target_sid)
