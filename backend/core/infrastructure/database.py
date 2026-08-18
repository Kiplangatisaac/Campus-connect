from typing import Optional

try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    AsyncIOMotorClient = None
    AsyncIOMotorDatabase = None

from config import settings


class DatabaseSessionManager:
    """MongoDB database session manager."""

    _instance: Optional["DatabaseSessionManager"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """Connect to MongoDB."""
        if self._client is None:
            self._client = AsyncIOMotorClient(settings.MONGODB_URI)
            self._database = self._client[settings.DATABASE_NAME]
            # Create indexes
            await self._create_indexes()

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._database

    def get_collection(self, name: str):
        """Get a collection."""
        return self.database[name]

    async def _create_indexes(self):
        """Create database indexes."""
        # Users
        await self.database.users.create_index("email", unique=True)
        await self.database.users.create_index("faculty")
        await self.database.users.create_index("role")

        # Study Groups
        await self.database.study_groups.create_index("creator_id")
        await self.database.study_groups.create_index("faculty")
        await self.database.study_groups.create_index("status")

        # Group Memberships
        await self.database.group_memberships.create_index(
            [("group_id", 1), ("user_id", 1)], unique=True
        )
        await self.database.group_memberships.create_index("user_id")

        # Ebooks
        await self.database.ebooks.create_index("faculty")
        await self.database.ebooks.create_index("uploaded_by")
        await self.database.ebooks.create_index([("$**", "text")])

        # Ebook Chunks
        await self.database.ebook_chunks.create_index("ebook_id")

        # Coding Sessions
        await self.database.coding_sessions.create_index("group_id")
        await self.database.coding_sessions.create_index("status")

        # AI Queries
        await self.database.ai_queries.create_index("user_id")
        await self.database.ai_queries.create_index("query_hash")

        # AI Quotas
        await self.database.ai_quotas.create_index("user_id", unique=True)

        # Messages
        await self.database.messages.create_index(
            [("conversation_id", 1), ("created_at", -1)]
        )

        # Conversations
        await self.database.conversations.create_index("participants")


# Singleton instance
db_manager = DatabaseSessionManager()
