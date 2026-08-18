from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional, List
from ...core.application.coding_service import CodingWorkspaceServiceImpl
from ...core.infrastructure import CodingSessionRepositoryImpl
from ...auth import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/api/coding", tags=["Coding Workspaces"])


class StartSessionRequest(BaseModel):
    group_id: str
    stack: str = "python"


class SessionResponse(BaseModel):
    session_id: str
    status: str
    creator: str
    stack: str
    participants: int
    has_edit_lock: bool
    current_editor: Optional[str]
    created_at: str
    last_activity: str


class CodeUpdateRequest(BaseModel):
    code: str


class CheckpointRequest(BaseModel):
    name: str


def get_coding_service():
    repo = CodingSessionRepositoryImpl()
    return CodingWorkspaceServiceImpl(repo)


@router.post("/start", response_model=SessionResponse)
async def start_session(
    request: StartSessionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: CodingWorkspaceServiceImpl = Depends(get_coding_service),
):
    session = await service.start_session(
        group_id=request.group_id,
        user_id=credentials.credentials,
        stack=request.stack,
    )
    return SessionResponse(
        session_id=session.id,
        status=session.status.value,
        creator=session.creator_id,
        stack=session.stack.value,
        participants=session.participant_count,
        has_edit_lock=session.has_edit_lock,
        current_editor=session.current_editor,
        created_at=session.created_at.isoformat(),
        last_activity=session.last_activity.isoformat(),
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: CodingWorkspaceServiceImpl = Depends(get_coding_service),
):
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session.id,
        status=session.status.value,
        creator=session.creator_id,
        stack=session.stack.value,
        participants=session.participant_count,
        has_edit_lock=session.has_edit_lock,
        current_editor=session.current_editor,
        created_at=session.created_at.isoformat(),
        last_activity=session.last_activity.isoformat(),
    )


@router.post("/{session_id}/stop")
async def stop_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: CodingWorkspaceServiceImpl = Depends(get_coding_service),
):
    success = await service.stop_session(session_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not stop session")
    return {"message": "Session stopped"}


@router.post("/{session_id}/edit")
async def request_edit(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: CodingWorkspaceServiceImpl = Depends(get_coding_service),
):
    success = await service.request_edit(session_id, credentials.credentials)
    if not success:
        raise HTTPException(status_code=400, detail="Could not acquire edit lock")
    return {"message": "Edit lock acquired"}


@router.post("/{session_id}/release")
async def release_edit(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: CodingWorkspaceServiceImpl = Depends(get_coding_service),
):
    success = await service.release_edit(session_id, credentials.credentials)
    if not success:
        raise HTTPException(status_code=400, detail="Could not release edit lock")
    return {"message": "Edit lock released"}


@router.post("/{session_id}/code")
async def update_code(
    session_id: str,
    request: CodeUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: CodingWorkspaceServiceImpl = Depends(get_coding_service),
):
    success = await service.update_code(session_id, credentials.credentials, request.code)
    if not success:
        raise HTTPException(status_code=400, detail="Could not update code")
    return {"message": "Code updated"}


@router.post("/{session_id}/checkpoint")
async def save_checkpoint(
    session_id: str,
    request: CheckpointRequest,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: CodingWorkspaceServiceImpl = Depends(get_coding_service),
):
    checkpoint = await service.save_checkpoint(session_id, request.name)
    if not checkpoint:
        raise HTTPException(status_code=400, detail="Could not save checkpoint")
    return {"checkpoint": checkpoint}


@router.post("/{session_id}/restore/{checkpoint_name}")
async def restore_checkpoint(
    session_id: str,
    checkpoint_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: CodingWorkspaceServiceImpl = Depends(get_coding_service),
):
    success = await service.restore_checkpoint(session_id, checkpoint_name)
    if not success:
        raise HTTPException(status_code=400, detail="Could not restore checkpoint")
    return {"message": "Checkpoint restored"}
