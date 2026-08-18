from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.moment import Moment, MomentLike, MomentComment
from ..limiter import limiter

router = APIRouter(prefix="/moments", tags=["Moments"])

class MomentCreate(BaseModel):
    content: str
    visibility: str = "public"

class MomentResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str]
    content: str
    image_url: Optional[str]
    likes_count: int
    comments_count: int
    created_at: datetime
    is_liked: bool

@router.get("/", response_model=list[MomentResponse])
@limiter.limit("30/minute")
async def get_moments(
    request: Request,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    stmt = (
        select(
            Moment,
            User.full_name,
            User.avatar_url,
            func.count(MomentLike.id).label('likes_count'),
            func.count(MomentComment.id).label('comments_count')
        )
        .join(User, Moment.user_id == User.id)
        .outerjoin(MomentLike, MomentLike.moment_id == Moment.id)
        .outerjoin(MomentComment, MomentComment.moment_id == Moment.id)
        .group_by(Moment.id)
        .order_by(Moment.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    moments = []
    for row in rows:
        moment = row[0]
        likes_count = row[3]
        comments_count = row[4]
        
        like_check = await db.execute(
            select(MomentLike.id).where(
                and_(MomentLike.moment_id == moment.id, MomentLike.user_id == current_user.id)
            )
        )
        is_liked = like_check.first() is not None
        
        moments.append(MomentResponse(
            id=moment.id,
            user_id=moment.user_id,
            user_name=row[1],
            user_avatar=row[2],
            content=moment.content,
            image_url=moment.image_url,
            likes_count=likes_count,
            comments_count=comments_count,
            created_at=moment.created_at,
            is_liked=is_liked
        ))
    
    return moments

@router.post("/", response_model=MomentResponse)
@limiter.limit("10/minute")
async def create_moment(
    request: Request,
    moment: MomentCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    new_moment = Moment(
        user_id=current_user.id,
        content=moment.content,
        visibility=moment.visibility
    )
    db.add(new_moment)
    await db.flush()
    
    return MomentResponse(
        id=new_moment.id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_avatar=current_user.avatar_url,
        content=new_moment.content,
        image_url=None,
        likes_count=0,
        comments_count=0,
        created_at=new_moment.created_at or datetime.now(),
        is_liked=False
    )

@router.post("/{moment_id}/like")
@limiter.limit("30/minute")
async def like_moment(
    request: Request,
    moment_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    existing = await db.execute(
        select(MomentLike).where(
            and_(MomentLike.moment_id == moment_id, MomentLike.user_id == current_user.id)
        )
    )
    like = existing.scalar_one_or_none()
    
    if like:
        await db.delete(like)
        await db.flush()
        return {"liked": False}
    else:
        new_like = MomentLike(moment_id=moment_id, user_id=current_user.id)
        db.add(new_like)
        await db.flush()
        return {"liked": True}
