"""Theme management routes."""

import json
import sqlite3
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from ..dependencies import get_current_user
from ..models.user import User
from ..limiter import limiter
from ..config import settings

router = APIRouter(prefix="/themes", tags=["Themes"])


DEFAULT_THEMES = [
    {"name": "Default KyU", "colors": {"primary": "#1a6b3c", "secondary": "#2ecc71", "accent": "#27ae60", "background": "#f5f5f5", "text": "#333333", "chatBubble": "#1a6b3c", "chatBackground": "#ffffff", "sidebarBackground": "#1a1a2e", "headerBackground": "#1a6b3c", "sentMessageColor": "#1a6b3c", "receivedMessageColor": "#e0e0e0", "readStatusColor": "#2ecc71", "deliveredStatusColor": "#3498db", "sentStatusColor": "#999999"}, "isDefault": True, "isActive": True},
    {"name": "Dark Mode", "colors": {"primary": "#bb86fc", "secondary": "#03dac6", "accent": "#cf6679", "background": "#121212", "text": "#e0e0e0", "chatBubble": "#bb86fc", "chatBackground": "#1e1e1e", "sidebarBackground": "#1a1a2e", "headerBackground": "#1e1e1e", "sentMessageColor": "#bb86fc", "receivedMessageColor": "#2d2d2d", "readStatusColor": "#03dac6", "deliveredStatusColor": "#bb86fc", "sentStatusColor": "#666666"}, "isDefault": False, "isActive": False},
    {"name": "Light Mode", "colors": {"primary": "#1976d2", "secondary": "#42a5f5", "accent": "#ff7043", "background": "#ffffff", "text": "#212121", "chatBubble": "#1976d2", "chatBackground": "#f5f5f5", "sidebarBackground": "#ffffff", "headerBackground": "#1976d2", "sentMessageColor": "#1976d2", "receivedMessageColor": "#e8e8e8", "readStatusColor": "#4caf50", "deliveredStatusColor": "#2196f3", "sentStatusColor": "#9e9e9e"}, "isDefault": False, "isActive": False},
    {"name": "KyU Green", "colors": {"primary": "#2e7d32", "secondary": "#66bb6a", "accent": "#ffca28", "background": "#e8f5e9", "text": "#1b5e20", "chatBubble": "#2e7d32", "chatBackground": "#f1f8e9", "sidebarBackground": "#1b5e20", "headerBackground": "#2e7d32", "sentMessageColor": "#2e7d32", "receivedMessageColor": "#c8e6c9", "readStatusColor": "#4caf50", "deliveredStatusColor": "#66bb6a", "sentStatusColor": "#a5d6a7"}, "isDefault": False, "isActive": False},
    {"name": "Ocean Blue", "colors": {"primary": "#0277bd", "secondary": "#4fc3f7", "accent": "#ff7043", "background": "#e1f5fe", "text": "#01579b", "chatBubble": "#0277bd", "chatBackground": "#e8f4fd", "sidebarBackground": "#01579b", "headerBackground": "#0277bd", "sentMessageColor": "#0277bd", "receivedMessageColor": "#b3e5fc", "readStatusColor": "#4caf50", "deliveredStatusColor": "#4fc3f7", "sentStatusColor": "#81d4fa"}, "isDefault": False, "isActive": False},
    {"name": "Forest", "colors": {"primary": "#33691e", "secondary": "#8bc34a", "accent": "#ffc107", "background": "#f1f8e9", "text": "#33691e", "chatBubble": "#33691e", "chatBackground": "#e8f5e9", "sidebarBackground": "#1b5e20", "headerBackground": "#33691e", "sentMessageColor": "#33691e", "receivedMessageColor": "#dcedc8", "readStatusColor": "#8bc34a", "deliveredStatusColor": "#aed581", "sentStatusColor": "#c5e1a5"}, "isDefault": False, "isActive": False},
    {"name": "Sunset", "colors": {"primary": "#e65100", "secondary": "#ff9800", "accent": "#ff5722", "background": "#fff3e0", "text": "#bf360c", "chatBubble": "#e65100", "chatBackground": "#fff8e1", "sidebarBackground": "#bf360c", "headerBackground": "#e65100", "sentMessageColor": "#e65100", "receivedMessageColor": "#ffe0b2", "readStatusColor": "#ff9800", "deliveredStatusColor": "#ffb74d", "sentStatusColor": "#ffcc80"}, "isDefault": False, "isActive": False},
    {"name": "KyU Blue", "colors": {"primary": "#1565c0", "secondary": "#42a5f5", "accent": "#ffca28", "background": "#e3f2fd", "text": "#0d47a1", "chatBubble": "#1565c0", "chatBackground": "#e8f4fd", "sidebarBackground": "#0d47a1", "headerBackground": "#1565c0", "sentMessageColor": "#1565c0", "receivedMessageColor": "#bbdefb", "readStatusColor": "#4caf50", "deliveredStatusColor": "#42a5f5", "sentStatusColor": "#90caf9"}, "isDefault": False, "isActive": False},
]


def _get_db():
    import re
    import os
    
    db_url = settings.SYNC_DATABASE_URL if hasattr(settings, 'SYNC_DATABASE_URL') else settings.DATABASE_URL
    
    # For SQLite databases
    if 'sqlite' in db_url.lower():
        match = re.search(r'sqlite:///([^?]+)', db_url)
        if match:
            db_path = match.group(1)
            # Handle relative paths
            if not db_path.startswith('/'):
                db_path = os.path.abspath(db_path)
        else:
            db_path = db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
            if not db_path.startswith('/'):
                db_path = os.path.abspath(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # For PostgreSQL and other databases - use SQLAlchemy async
    # Fall back to SQLite in-memory for themes if no SQLite available
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_default_themes(conn):
    cursor = conn.execute("SELECT COUNT(*) FROM themes")
    count = cursor.fetchone()[0]
    if count == 0:
        for theme in DEFAULT_THEMES:
            conn.execute(
                "INSERT INTO themes (name, colors, isDefault, isActive, createdAt) VALUES (?, ?, ?, ?, ?)",
                (theme["name"], json.dumps(theme["colors"]), theme["isDefault"], theme["isActive"], datetime.utcnow().isoformat())
            )
        conn.commit()


class ThemeCreate(BaseModel):
    name: str
    colors: dict
    isDefault: bool = False

class ThemeUpdate(BaseModel):
    name: Optional[str] = None
    colors: Optional[dict] = None
    isActive: Optional[bool] = None

class UserThemeUpdate(BaseModel):
    themeId: Optional[int] = None
    customizations: Optional[dict] = None


@router.on_event("startup")
async def startup_themes():
    conn = _get_db()
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            colors TEXT NOT NULL,
            isDefault BOOLEAN DEFAULT 0,
            isActive BOOLEAN DEFAULT 0,
            createdBy INTEGER,
            createdAt TEXT,
            updatedAt TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS user_themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER UNIQUE NOT NULL,
            themeId INTEGER,
            customizations TEXT,
            FOREIGN KEY (themeId) REFERENCES themes(id)
        )''')
        conn.commit()
        _ensure_default_themes(conn)
    finally:
        conn.close()


@router.get("/")
@limiter.limit("30/minute")
async def list_themes(request: Request):
    conn = _get_db()
    try:
        themes = conn.execute("SELECT * FROM themes").fetchall()
        return [{"id": t["id"], "name": t["name"], "colors": json.loads(t["colors"]), "isDefault": bool(t["isDefault"]), "isActive": bool(t["isActive"])} for t in themes]
    finally:
        conn.close()


@router.get("/active")
@limiter.limit("30/minute")
async def get_active_theme(request: Request):
    conn = _get_db()
    try:
        theme = conn.execute("SELECT * FROM themes WHERE isActive = 1").fetchone()
        if not theme:
            theme = conn.execute("SELECT * FROM themes WHERE isDefault = 1").fetchone()
        if not theme:
            return {"id": 1, "name": "Default KyU", "colors": DEFAULT_THEMES[0]["colors"]}
        return {"id": theme["id"], "name": theme["name"], "colors": json.loads(theme["colors"])}
    finally:
        conn.close()


@router.get("/user")
@limiter.limit("30/minute")
async def get_user_theme(request: Request, current_user: User = Depends(get_current_user)):
    conn = _get_db()
    try:
        ut = conn.execute("SELECT * FROM user_themes WHERE userId = ?", (current_user.id,)).fetchone()
        if not ut:
            return {"themeId": None, "customizations": {}}
        return {"themeId": ut["themeId"], "customizations": json.loads(ut["customizations"]) if ut["customizations"] else {}}
    finally:
        conn.close()


@router.post("/user")
@limiter.limit("10/minute")
async def save_user_theme(request: Request, data: UserThemeUpdate, current_user: User = Depends(get_current_user)):
    conn = _get_db()
    try:
        existing = conn.execute("SELECT id FROM user_themes WHERE userId = ?", (current_user.id,)).fetchone()
        if existing:
            conn.execute("UPDATE user_themes SET themeId = ?, customizations = ? WHERE userId = ?",
                         (data.themeId, json.dumps(data.customizations) if data.customizations else None, current_user.id))
        else:
            conn.execute("INSERT INTO user_themes (userId, themeId, customizations) VALUES (?, ?, ?)",
                         (current_user.id, data.themeId, json.dumps(data.customizations) if data.customizations else None))
        conn.commit()
        return {"success": True}
    finally:
        conn.close()


@router.post("/")
@limiter.limit("5/minute")
async def create_theme(request: Request, data: ThemeCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    conn = _get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO themes (name, colors, isDefault, isActive, createdBy, createdAt) VALUES (?, ?, ?, ?, ?, ?)",
            (data.name, json.dumps(data.colors), data.isDefault, False, current_user.id, datetime.utcnow().isoformat())
        )
        conn.commit()
        return {"id": cursor.lastrowid, "name": data.name, "colors": data.colors}
    finally:
        conn.close()


@router.put("/{theme_id}")
@limiter.limit("10/minute")
async def update_theme(request: Request, theme_id: int, data: ThemeUpdate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    conn = _get_db()
    try:
        updates = []
        params = []
        if data.name:
            updates.append("name = ?")
            params.append(data.name)
        if data.colors:
            updates.append("colors = ?")
            params.append(json.dumps(data.colors))
        if data.isActive is not None:
            if data.isActive:
                conn.execute("UPDATE themes SET isActive = 0")
            updates.append("isActive = ?")
            params.append(data.isActive)
        if updates:
            updates.append("updatedAt = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(theme_id)
            conn.execute(f"UPDATE themes SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
        return {"success": True}
    finally:
        conn.close()


@router.delete("/{theme_id}")
@limiter.limit("5/minute")
async def delete_theme(request: Request, theme_id: int, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    conn = _get_db()
    try:
        theme = conn.execute("SELECT isDefault FROM themes WHERE id = ?", (theme_id,)).fetchone()
        if theme and theme["isDefault"]:
            raise HTTPException(status_code=400, detail="Cannot delete default theme")
        conn.execute("DELETE FROM themes WHERE id = ?", (theme_id,))
        conn.commit()
        return {"success": True}
    finally:
        conn.close()
