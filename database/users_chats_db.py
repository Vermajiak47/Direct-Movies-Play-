import motor.motor_asyncio
from info import (
    DATABASE_NAME, DATABASE_URI, DATABASE_URI2, IMDB, IMDB_TEMPLATE, MELCOW_NEW_USERS, 
    P_TTI_SHOW_OFF, SINGLE_BUTTON, SPELL_CHECK_REPLY, PROTECT_CONTENT, AUTO_DELETE, MAX_BTN, 
    AUTO_FFILTER, SHORTLINK_API, SHORTLINK_URL, IS_SHORTLINK, TUTORIAL, IS_TUTORIAL, VERIFY, 
    PM_SEARCH, MULTI_FSUB, DEENDAYAL_MOVIE_UPDATE_NOTIFICATION, LOG_CHANNEL
)
import datetime
import pytz  
from pymongo.errors import DuplicateKeyError
from pymongo import MongoClient
import logging

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# MongoDB connection
try:
    my_client = MongoClient(DATABASE_URI)
    mydb = my_client["filename"]
    logger.info("Connected to MongoDB successfully.")
except Exception as e:
    logger.exception("Failed to connect to MongoDB!", exc_info=True)


async def add_name(user_id: int, filename: str) -> bool:
    """Adds a filename entry for a user if it doesn't already exist."""
    try:
        user_db = mydb[str(user_id)]
        existing_user = await user_db.find_one({'_id': filename})

        if existing_user:
            return False
        
        await user_db.insert_one({'_id': filename})
        return True

    except Exception as e:
        logger.exception(f"Error adding filename for user {user_id}: {e}")
        return False


async def delete_all_msg(user_id: int):
    """Deletes all messages/files associated with a user."""
    try:
        user_db = mydb[str(user_id)]
        await user_db.delete_many({})
        logger.info(f"Deleted all messages for user {user_id}.")
    except Exception as e:
        logger.exception(f"Error deleting messages for user {user_id}: {e}")


class Database:
    def __init__(self, uri: str, database_name: str):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.grp = self.db.groups
        self.users = self.db.uersz
        self.req = self.db.requests
        self.botcol = self.db["deendayal"]  
        self.bot_id_col = self.db["bot_id"] 

    async def find_join_req(self, id: int) -> bool:
        """Checks if a join request exists."""
        return bool(await self.req.find_one({'id': id})) 

    async def add_join_req(self, id: int):
        """Adds a new join request."""
        await self.req.insert_one({'id': id})

    async def del_join_req(self):
        """Deletes all join requests."""
        await self.req.delete_many({})

    async def update_verification(self, id: int, date: str, time: str):
        """Updates verification status for a user."""
        status = {'date': str(date), 'time': str(time)}
        await self.col.update_one({'id': id}, {'$set': {'verification_status': status}})

    async def get_verified(self, id: int) -> dict:
        """Retrieves verification status of a user."""
        default = {'date': "1999-12-31", 'time': "23:59:59"}
        user = await self.col.find_one({'id': id}, {'verification_status': 1})
        return user.get("verification_status", default) if user else default    

    async def add_user(self, id: int, name: str):
        """Adds a new user."""
        user = {
            'id': id,
            'name': name,
            'ban_status': {'is_banned': False, 'ban_reason': ""},
        }
        await self.col.insert_one(user)

    async def is_user_exist(self, id: int) -> bool:
        """Checks if a user exists."""
        return bool(await self.col.find_one({'id': id}))

    async def total_users_count(self) -> int:
        """Returns total number of users."""
        return await self.col.count_documents({})

    async def remove_ban(self, id: int):
        """Removes ban from a user."""
        await self.col.update_one({'id': id}, {'$set': {'ban_status': {'is_banned': False, 'ban_reason': ''}}})

    async def ban_user(self, user_id: int, ban_reason: str = "No Reason"):
        """Bans a user."""
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': {'is_banned': True, 'ban_reason': ban_reason}}})

    async def get_ban_status(self, id: int) -> dict:
        """Returns ban status of a user."""
        default = {'is_banned': False, 'ban_reason': ''}
        user = await self.col.find_one({'id': id}, {'ban_status': 1})
        return user.get('ban_status', default) if user else default

    async def total_chat_count(self) -> int:
        """Returns total number of chats."""
        return await self.grp.count_documents({})

    async def get_user(self, user_id: int) -> dict:
        """Retrieves user data."""
        return await self.users.find_one({"id": user_id})

    async def update_user(self, user_data: dict):
        """Updates user data."""
        await self.users.update_one({"id": user_data["id"]}, {"$set": user_data}, upsert=True)

    async def has_premium_access(self, user_id: int) -> bool:
        """Checks if a user has premium access."""
        user_data = await self.get_user(user_id)
        if user_data:
            expiry_time = user_data.get("expiry_time")
            if isinstance(expiry_time, datetime.datetime) and datetime.datetime.now() <= expiry_time:
                return True
            await self.users.update_one({"id": user_id}, {"$set": {"expiry_time": None}})
        return False

    async def get_expired(self, current_time: datetime.datetime) -> list:
        """Returns a list of expired users."""
        expired_users = []
        async for user in self.users.find({"expiry_time": {"$lt": current_time}}):
            expired_users.append(user)
        return expired_users

    async def pm_search_status(self, bot_id: int) -> bool:
        """Gets the PM search status of a bot."""
        bot = await self.botcol.find_one({'id': bot_id}, {'bot_pm_search': 1})
        return bot.get('bot_pm_search', PM_SEARCH) if bot else PM_SEARCH

    async def update_pm_search_status(self, bot_id: int, enable: bool):
        """Updates the PM search status of a bot."""
        await self.botcol.update_one({'id': bot_id}, {'$set': {'bot_pm_search': enable}}, upsert=True)

    async def all_premium_users(self) -> int:
        """Returns count of premium users."""
        return await self.users.count_documents({"expiry_time": {"$gt": datetime.datetime.now()}})

# Initialize the database connections
db = Database(DATABASE_URI, DATABASE_NAME)
db2 = Database(DATABASE_URI2, DATABASE_NAME)
