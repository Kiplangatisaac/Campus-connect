from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from ..database import Base

class Moment(Base):
    __tablename__ = "moments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    visibility = Column(String(20), default="public")
    created_at = Column(DateTime, server_default=func.now())

class MomentLike(Base):
    __tablename__ = "moment_likes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    moment_id = Column(Integer, ForeignKey("moments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class MomentComment(Base):
    __tablename__ = "moment_comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    moment_id = Column(Integer, ForeignKey("moments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
