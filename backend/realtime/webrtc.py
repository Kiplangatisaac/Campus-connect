import socketio
from typing import Optional

from ..realtime.socket_handler import sio, online_users, user_sids

webrtc_sessions: dict[str, dict] = {}


@sio.event
async def webrtc_offer(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    target_user_id = data.get("target_user_id")
    offer = data.get("offer")
    call_type = data.get("call_type", "video")

    if not target_user_id or not offer:
        await sio.emit("error", {"message": "target_user_id and offer required"}, room=sid)
        return

    if target_user_id not in online_users:
        await sio.emit("error", {"message": "Target user is offline"}, room=sid)
        return

    session_id = f"call_{min(user_id, target_user_id)}_{max(user_id, target_user_id)}"
    webrtc_sessions[session_id] = {
        "caller_id": user_id,
        "callee_id": target_user_id,
        "call_type": call_type,
        "status": "ringing",
    }

    target_sid = online_users[target_user_id]
    await sio.emit("webrtc_offer", {
        "from_user_id": user_id,
        "offer": offer,
        "call_type": call_type,
        "session_id": session_id,
    }, room=target_sid)


@sio.event
async def webrtc_answer(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    target_user_id = data.get("target_user_id")
    answer = data.get("answer")
    session_id = data.get("session_id")

    if not target_user_id or not answer:
        await sio.emit("error", {"message": "target_user_id and answer required"}, room=sid)
        return

    if target_user_id not in online_users:
        await sio.emit("error", {"message": "Target user is offline"}, room=sid)
        return

    if session_id and session_id in webrtc_sessions:
        webrtc_sessions[session_id]["status"] = "connected"

    target_sid = online_users[target_user_id]
    await sio.emit("webrtc_answer", {
        "from_user_id": user_id,
        "answer": answer,
        "session_id": session_id,
    }, room=target_sid)


@sio.event
async def webrtc_ice_candidate(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    target_user_id = data.get("target_user_id")
    candidate = data.get("candidate")
    session_id = data.get("session_id")

    if not target_user_id or not candidate:
        return

    if target_user_id not in online_users:
        return

    target_sid = online_users[target_user_id]
    await sio.emit("webrtc_ice_candidate", {
        "from_user_id": user_id,
        "candidate": candidate,
        "session_id": session_id,
    }, room=target_sid)


@sio.event
async def webrtc_reject(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    target_user_id = data.get("target_user_id")
    session_id = data.get("session_id")

    if session_id and session_id in webrtc_sessions:
        webrtc_sessions[session_id]["status"] = "rejected"

    if target_user_id and target_user_id in online_users:
        target_sid = online_users[target_user_id]
        await sio.emit("webrtc_rejected", {
            "from_user_id": user_id,
            "session_id": session_id,
        }, room=target_sid)


@sio.event
async def webrtc_end(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    target_user_id = data.get("target_user_id")
    session_id = data.get("session_id")

    if session_id and session_id in webrtc_sessions:
        del webrtc_sessions[session_id]

    if target_user_id and target_user_id in online_users:
        target_sid = online_users[target_user_id]
        await sio.emit("webrtc_ended", {
            "from_user_id": user_id,
            "session_id": session_id,
        }, room=target_sid)


@sio.event
async def webrtc_mute(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    target_user_id = data.get("target_user_id")
    is_muted = data.get("is_muted", False)
    media_type = data.get("media_type", "audio")

    if target_user_id and target_user_id in online_users:
        target_sid = online_users[target_user_id]
        await sio.emit("webrtc_mute", {
            "from_user_id": user_id,
            "is_muted": is_muted,
            "media_type": media_type,
        }, room=target_sid)


@sio.event
async def webrtc_video_toggle(sid, data):
    user_id = user_sids.get(sid)
    if not user_id:
        return

    target_user_id = data.get("target_user_id")
    is_video_on = data.get("is_video_on", True)

    if target_user_id and target_user_id in online_users:
        target_sid = online_users[target_user_id]
        await sio.emit("webrtc_video_toggle", {
            "from_user_id": user_id,
            "is_video_on": is_video_on,
        }, room=target_sid)
