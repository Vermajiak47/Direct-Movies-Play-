import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI

# Initialize Logger
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri, db_name):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.col = self.db.user
        self.config_col = self.db.configuration

    async def update_top_messages(self, user_id, message_text):
        """Updates the count of a specific message for a user."""
        try:
            result = await self.col.update_one(
                {"user_id": user_id, "messages.text": message_text},
                {"$inc": {"messages.$.count": 1}}
            )
            if result.matched_count == 0:
                await self.col.update_one(
                    {"user_id": user_id},
                    {"$push": {"messages": {"text": message_text, "count": 1}}},
                    upsert=True
                )
        except Exception as e:
            logger.error(f"Error updating top messages: {e}")

    async def get_top_messages(self, limit=30):
        """Retrieves the most frequently sent messages."""
        try:
            pipeline = [
                {"$unwind": "$messages"},
                {"$group": {"_id": "$messages.text", "count": {"$sum": "$messages.count"}}},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]
            results = await self.col.aggregate(pipeline).to_list(limit)
            return [result["_id"] for result in results]
        except Exception as e:
            logger.error(f"Error fetching top messages: {e}")
            return []

    async def delete_all_messages(self):
        """Deletes all stored messages from the database."""
        try:
            await self.col.delete_many({})
        except Exception as e:
            logger.error(f"Error deleting messages: {e}")

    def create_configuration_data(self):
        """Creates default configuration data."""
        return {
            "maintenance_mode": False,
            "auto_accept": True,
            "one_link": True,
            "one_link_one_file_group": False,
            "private_filter": True,
            "group_filter": True,
            "terms": True,
            "spoll_check": True,
            "forcesub": True,
            "shortner": None,
            "no_ads": False,
            "advertisement": None,
        }

    async def ensure_config_initialized(self):
        """Ensures configuration data is initialized in the database."""
        if not await self.config_col.find_one({}):
            await self.config_col.insert_one(self.create_configuration_data())

    async def update_advertisement(self, ads_string=None, ads_name=None, expiry=None, impression=None):
        """Updates the advertisement details in the configuration."""
        try:
            await self.ensure_config_initialized()
            await self.config_col.update_one(
                {},
                {"$set": {"advertisement": {
                    "ads_string": ads_string,
                    "ads_name": ads_name,
                    "expiry": expiry,
                    "impression_count": impression
                }}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating advertisement: {e}")

    async def update_advertisement_impression(self, impression):
        """Updates the impression count for the advertisement."""
        try:
            await self.config_col.update_one({}, {"$set": {"advertisement.impression_count": impression}}, upsert=True)
        except Exception as e:
            logger.error(f"Error updating advertisement impressions: {e}")

    async def get_advertisement(self):
        """Retrieves the advertisement details."""
        try:
            await self.ensure_config_initialized()
            config = await self.config_col.find_one({})
            ad = config.get("advertisement", {})
            return ad.get("ads_string"), ad.get("ads_name"), ad.get("impression_count")
        except Exception as e:
            logger.error(f"Error fetching advertisement: {e}")
            return None, None, None

    async def reset_advertisement_if_expired(self):
        """Resets the advertisement if it has expired or impressions are 0."""
        try:
            config = await self.config_col.find_one({})
            if not config:
                return

            ad = config.get("advertisement")
            if ad:
                expiry = ad.get("expiry")
                impression_count = ad.get("impression_count", 0)

                # Check expiration and reset if needed
                if impression_count == 0 or (expiry and datetime.utcnow() > expiry):
                    await self.config_col.update_one({}, {"$set": {"advertisement": None}})
        except Exception as e:
            logger.error(f"Error resetting expired advertisement: {e}")

    async def update_configuration(self, key, value):
        """Updates a specific configuration setting."""
        try:
            await self.ensure_config_initialized()
            await self.config_col.update_one({}, {"$set": {key: value}}, upsert=True)
        except Exception as e:
            logger.error(f"Error updating configuration '{key}': {e}")

    async def get_configuration_value(self, key):
        """Retrieves a specific configuration value."""
        try:
            await self.ensure_config_initialized()
            config = await self.config_col.find_one({})
            return config.get(key, False)
        except Exception as e:
            logger.error(f"Error fetching configuration '{key}': {e}")
            return False

# Initialize Database Connection
mdb = Database(DATABASE_URI, "admin_database")
