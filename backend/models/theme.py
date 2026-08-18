"""Theme SQLAlchemy models."""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class Theme(Base):
    __tablename__ = "themes"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    colors = Column(JSON, nullable=False)
    isDefault = Column(Boolean, default=False)
    isActive = Column(Boolean, default=False)
    createdBy = Column(String, ForeignKey("users.id"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "colors": self.colors,
            "isDefault": self.isDefault,
            "isActive": self.isActive,
            "createdBy": self.createdBy,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "updatedAt": self.updatedAt.isoformat() if self.updatedAt else None,
        }


class UserTheme(Base):
    __tablename__ = "user_themes"

    id = Column(String, primary_key=True)
    userId = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    themeId = Column(String, ForeignKey("themes.id"), nullable=False)
    customizations = Column(JSON, default=dict)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    theme = relationship("Theme", foreign_keys=[themeId])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "userId": self.userId,
            "themeId": self.themeId,
            "customizations": self.customizations,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "updatedAt": self.updatedAt.isoformat() if self.updatedAt else None,
            "theme": self.theme.to_dict() if self.theme else None,
        }


DEFAULT_THEMES = [
    {
        "name": "Default KyU",
        "colors": {
            "primary": "#1B5E20",
            "secondary": "#4CAF50",
            "accent": "#81C784",
            "background": "#FAFAFA",
            "text": "#212121",
            "chatBubble": "#E8F5E9",
            "chatBackground": "#F5F5F5",
            "sidebarBackground": "#FFFFFF",
            "headerBackground": "#1B5E20",
            "sentMessageColor": "#1B5E20",
            "receivedMessageColor": "#FFFFFF",
            "readStatusColor": "#4CAF50",
            "deliveredStatusColor": "#9E9E9E",
            "sentStatusColor": "#BDBDBD",
        },
        "isDefault": True,
        "isActive": True,
    },
    {
        "name": "Dark Mode",
        "colors": {
            "primary": "#BB86FC",
            "secondary": "#03DAC6",
            "accent": "#CF6679",
            "background": "#121212",
            "text": "#E0E0E0",
            "chatBubble": "#1E1E1E",
            "chatBackground": "#0D0D0D",
            "sidebarBackground": "#1A1A1A",
            "headerBackground": "#1F1F1F",
            "sentMessageColor": "#BB86FC",
            "receivedMessageColor": "#2C2C2C",
            "readStatusColor": "#03DAC6",
            "deliveredStatusColor": "#616161",
            "sentStatusColor": "#424242",
        },
        "isDefault": False,
        "isActive": False,
    },
    {
        "name": "Light Mode",
        "colors": {
            "primary": "#6200EE",
            "secondary": "#03DAC6",
            "accent": "#018786",
            "background": "#FFFFFF",
            "text": "#000000",
            "chatBubble": "#F0F0F0",
            "chatBackground": "#FAFAFA",
            "sidebarBackground": "#F5F5F5",
            "headerBackground": "#6200EE",
            "sentMessageColor": "#6200EE",
            "receivedMessageColor": "#F0F0F0",
            "readStatusColor": "#03DAC6",
            "deliveredStatusColor": "#BDBDBD",
            "sentStatusColor": "#9E9E9E",
        },
        "isDefault": False,
        "isActive": False,
    },
    {
        "name": "KyU Green",
        "colors": {
            "primary": "#2E7D32",
            "secondary": "#66BB6A",
            "accent": "#A5D6A7",
            "background": "#F1F8E9",
            "text": "#1B5E20",
            "chatBubble": "#DCEDC8",
            "chatBackground": "#F9FBE7",
            "sidebarBackground": "#E8F5E9",
            "headerBackground": "#2E7D32",
            "sentMessageColor": "#2E7D32",
            "receivedMessageColor": "#FFFFFF",
            "readStatusColor": "#66BB6A",
            "deliveredStatusColor": "#A5D6A7",
            "sentStatusColor": "#C8E6C9",
        },
        "isDefault": False,
        "isActive": False,
    },
    {
        "name": "KyU Blue",
        "colors": {
            "primary": "#1565C0",
            "secondary": "#42A5F5",
            "accent": "#90CAF9",
            "background": "#E3F2FD",
            "text": "#0D47A1",
            "chatBubble": "#BBDEFB",
            "chatBackground": "#E1F5FE",
            "sidebarBackground": "#E3F2FD",
            "headerBackground": "#1565C0",
            "sentMessageColor": "#1565C0",
            "receivedMessageColor": "#FFFFFF",
            "readStatusColor": "#42A5F5",
            "deliveredStatusColor": "#90CAF9",
            "sentStatusColor": "#BBDEFB",
        },
        "isDefault": False,
        "isActive": False,
    },
    {
        "name": "Ocean",
        "colors": {
            "primary": "#00695C",
            "secondary": "#26A69A",
            "accent": "#80CBC4",
            "background": "#E0F2F1",
            "text": "#004D40",
            "chatBubble": "#B2DFDB",
            "chatBackground": "#E0F7FA",
            "sidebarBackground": "#E0F2F1",
            "headerBackground": "#00695C",
            "sentMessageColor": "#00695C",
            "receivedMessageColor": "#FFFFFF",
            "readStatusColor": "#26A69A",
            "deliveredStatusColor": "#80CBC4",
            "sentStatusColor": "#B2DFDB",
        },
        "isDefault": False,
        "isActive": False,
    },
    {
        "name": "Forest",
        "colors": {
            "primary": "#33691E",
            "secondary": "#689F38",
            "accent": "#AED581",
            "background": "#F1F8E9",
            "text": "#1B5E20",
            "chatBubble": "#DCEDC8",
            "chatBackground": "#F9FBE7",
            "sidebarBackground": "#DCEDC8",
            "headerBackground": "#33691E",
            "sentMessageColor": "#33691E",
            "receivedMessageColor": "#FFFFFF",
            "readStatusColor": "#689F38",
            "deliveredStatusColor": "#AED581",
            "sentStatusColor": "#C5E1A5",
        },
        "isDefault": False,
        "isActive": False,
    },
    {
        "name": "Sunset",
        "colors": {
            "primary": "#E65100",
            "secondary": "#FF9800",
            "accent": "#FFB74D",
            "background": "#FFF3E0",
            "text": "#BF360C",
            "chatBubble": "#FFE0B2",
            "chatBackground": "#FFF8E1",
            "sidebarBackground": "#FFF3E0",
            "headerBackground": "#E65100",
            "sentMessageColor": "#E65100",
            "receivedMessageColor": "#FFFFFF",
            "readStatusColor": "#FF9800",
            "deliveredStatusColor": "#FFB74D",
            "sentStatusColor": "#FFCC80",
        },
        "isDefault": False,
        "isActive": False,
    },
]
