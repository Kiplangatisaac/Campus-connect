from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from ..database import get_db
from ..models.user import User
from ..models.bulletin import BulletinPost, BulletinComment
from ..schemas.bulletin import (
    BulletinPostCreate, BulletinPostUpdate, BulletinPostResponse,
    BulletinCommentCreate, BulletinCommentResponse,
    BulletinSearch, BulletinModeration
)
from ..dependencies import get_current_user, require_moderator_or_admin

router = APIRouter(prefix="/bulletin", tags=["Bulletin Board"])


@router.get("/posts", response_model=list[BulletinPostResponse])
async def list_posts(
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    author_id: Optional[int] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(BulletinPost).where(BulletinPost.is_active == True)

    if query:
        search_term = f"%{query}%"
        stmt = stmt.where(or_(BulletinPost.title.ilike(search_term), BulletinPost.content.ilike(search_term)))

    if category:
        stmt = stmt.where(BulletinPost.category == category)

    if author_id:
        stmt = stmt.where(BulletinPost.author_id == author_id)

    if is_pinned is not None:
        stmt = stmt.where(BulletinPost.is_pinned == is_pinned)

    stmt = stmt.order_by(BulletinPost.is_pinned.desc(), BulletinPost.created_at.desc())
    stmt = stmt.offset((page - 1) * limit).limit(limit)

    result = await db.execute(stmt)
    posts = result.scalars().all()

    responses = []
    for post in posts:
        comment_count = await db.scalar(
            select(func.count(BulletinComment.id)).where(
                BulletinComment.post_id == post.id,
                BulletinComment.is_active == True
            )
        )
        author = await db.get(User, post.author_id)
        response = BulletinPostResponse(
            id=post.id,
            title=post.title,
            content=post.content,
            category=post.category,
            image_url=post.image_url,
            author_id=post.author_id,
            author_name=author.full_name if author else "Unknown",
            author_avatar=author.avatar_url if author else None,
            is_pinned=post.is_pinned,
            is_active=post.is_active,
            views_count=post.views_count,
            comment_count=comment_count or 0,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )
        responses.append(response)

    return responses


@router.post("/posts", response_model=BulletinPostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: BulletinPostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post = BulletinPost(
        title=data.title,
        content=data.content,
        category=data.category,
        image_url=data.image_url,
        author_id=current_user.id,
    )
    db.add(post)
    await db.flush()
    await db.refresh(post)

    return BulletinPostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        category=post.category,
        image_url=post.image_url,
        author_id=post.author_id,
        author_name=current_user.full_name,
        author_avatar=current_user.avatar_url,
        is_pinned=post.is_pinned,
        is_active=post.is_active,
        views_count=post.views_count,
        comment_count=0,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.get("/posts/{post_id}", response_model=BulletinPostResponse)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BulletinPost).where(BulletinPost.id == post_id, BulletinPost.is_active == True)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    post.views_count += 1
    await db.flush()

    comment_count = await db.scalar(
        select(func.count(BulletinComment.id)).where(
            BulletinComment.post_id == post.id,
            BulletinComment.is_active == True
        )
    )

    author = await db.get(User, post.author_id)

    return BulletinPostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        category=post.category,
        image_url=post.image_url,
        author_id=post.author_id,
        author_name=author.full_name if author else "Unknown",
        author_avatar=author.avatar_url if author else None,
        is_pinned=post.is_pinned,
        is_active=post.is_active,
        views_count=post.views_count,
        comment_count=comment_count or 0,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.put("/posts/{post_id}", response_model=BulletinPostResponse)
async def update_post(
    post_id: int,
    data: BulletinPostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BulletinPost).where(BulletinPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.author_id != current_user.id and current_user.role.value not in ["admin", "moderator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)

    await db.flush()
    await db.refresh(post)

    author = await db.get(User, post.author_id)
    return BulletinPostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        category=post.category,
        image_url=post.image_url,
        author_id=post.author_id,
        author_name=author.full_name if author else "Unknown",
        author_avatar=author.avatar_url if author else None,
        is_pinned=post.is_pinned,
        is_active=post.is_active,
        views_count=post.views_count,
        comment_count=0,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BulletinPost).where(BulletinPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.author_id != current_user.id and current_user.role.value not in ["admin", "moderator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    post.is_active = False
    await db.flush()


@router.put("/posts/{post_id}/moderate", response_model=BulletinPostResponse)
async def moderate_post(
    post_id: int,
    data: BulletinModeration,
    moderator: User = Depends(require_moderator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BulletinPost).where(BulletinPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if data.is_pinned is not None:
        post.is_pinned = data.is_pinned
    if data.is_active is not None:
        post.is_active = data.is_active

    await db.flush()
    await db.refresh(post)

    author = await db.get(User, post.author_id)
    return BulletinPostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        category=post.category,
        image_url=post.image_url,
        author_id=post.author_id,
        author_name=author.full_name if author else "Unknown",
        author_avatar=author.avatar_url if author else None,
        is_pinned=post.is_pinned,
        is_active=post.is_active,
        views_count=post.views_count,
        comment_count=0,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.get("/posts/{post_id}/comments", response_model=list[BulletinCommentResponse])
async def list_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(BulletinComment)
        .where(
            BulletinComment.post_id == post_id,
            BulletinComment.is_active == True,
            BulletinComment.parent_id == None,
        )
        .order_by(BulletinComment.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(stmt)
    comments = result.scalars().all()

    responses = []
    for comment in comments:
        author = await db.get(User, comment.author_id)
        replies_count = await db.scalar(
            select(func.count(BulletinComment.id)).where(
                BulletinComment.parent_id == comment.id,
                BulletinComment.is_active == True
            )
        )
        responses.append(BulletinCommentResponse(
            id=comment.id,
            content=comment.content,
            post_id=comment.post_id,
            author_id=comment.author_id,
            author_name=author.full_name if author else "Unknown",
            author_avatar=author.avatar_url if author else None,
            parent_id=comment.parent_id,
            is_active=comment.is_active,
            replies_count=replies_count or 0,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        ))

    return responses


@router.post("/posts/{post_id}/comments", response_model=BulletinCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    data: BulletinCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post_check = await db.execute(
        select(BulletinPost).where(BulletinPost.id == post_id, BulletinPost.is_active == True)
    )
    if not post_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if data.parent_id:
        parent_check = await db.execute(
            select(BulletinComment).where(
                BulletinComment.id == data.parent_id,
                BulletinComment.post_id == post_id,
                BulletinComment.is_active == True
            )
        )
        if not parent_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found")

    comment = BulletinComment(
        content=data.content,
        post_id=post_id,
        author_id=current_user.id,
        parent_id=data.parent_id,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)

    return BulletinCommentResponse(
        id=comment.id,
        content=comment.content,
        post_id=comment.post_id,
        author_id=comment.author_id,
        author_name=current_user.full_name,
        author_avatar=current_user.avatar_url,
        parent_id=comment.parent_id,
        is_active=comment.is_active,
        replies_count=0,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BulletinComment).where(BulletinComment.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    if comment.author_id != current_user.id and current_user.role.value not in ["admin", "moderator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    comment.is_active = False
    await db.flush()
