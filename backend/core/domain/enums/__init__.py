from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    ADMIN = "admin"
    MODERATOR = "moderator"
    FACULTY = "faculty"


class GroupStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class GroupPrivacy(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class GroupMemberRole(str, Enum):
    MEMBER = "member"
    MODERATOR = "moderator"
    ADMIN = "admin"


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"


class NotificationType(str, Enum):
    MESSAGE = "message"
    GROUP_INVITE = "group_invite"
    GROUP_APPROVED = "group_approved"
    EVENT_REMINDER = "event_reminder"
    MENTION = "mention"
    SYSTEM = "system"


class CodingSessionStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AIQueryType(str, Enum):
    GENERAL = "general"
    COURSE = "course"
    CODE = "code"
    SUMMARY = "summary"
    FLASHCARD = "flashcard"
    TRANSLATION = "translation"


class EbookFormat(str, Enum):
    PDF = "pdf"
    EPUB = "epub"
    MOBI = "mobi"
    TXT = "txt"


class Faculty(str, Enum):
    ENGINEERING = "School of Engineering & Technology"
    BUSINESS = "School of Business & Education"
    HEALTH = "School of Health Sciences"
    COMPUTING = "School of Computing & Informatics"
    AGRICULTURE = "School of Agriculture"
    GENERAL = "General"


class AIProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    TERMINATED = "terminated"


class CodingStack(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
