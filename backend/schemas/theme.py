"""Theme Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel


class ThemeColors(BaseModel):
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    chatBubble: str
    chatBackground: str
    sidebarBackground: str
    headerBackground: str
    sentMessageColor: str
    receivedMessageColor: str
    readStatusColor: str
    deliveredStatusColor: str
    sentStatusColor: str


class ThemeCreate(BaseModel):
    name: str
    colors: ThemeColors
    isDefault: Optional[bool] = False
    isActive: Optional[bool] = False


class ThemeUpdate(BaseModel):
    name: Optional[str] = None
    colors: Optional[ThemeColors] = None
    isDefault: Optional[bool] = None
    isActive: Optional[bool] = None


class ThemeResponse(BaseModel):
    id: str
    name: str
    colors: ThemeColors
    isDefault: bool
    isActive: bool
    createdBy: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    class Config:
        from_attributes = True


class ThemeListResponse(BaseModel):
    themes: list[ThemeResponse]


class UserThemeUpdate(BaseModel):
    themeId: str
    customizations: Optional[dict] = None


class UserThemeResponse(BaseModel):
    themeId: Optional[str] = None
    theme: Optional[ThemeResponse] = None
    customizations: dict = {}
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    class Config:
        from_attributes = True
