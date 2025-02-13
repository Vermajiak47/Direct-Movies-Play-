from motor.motor_asyncio import AsyncIOMotorClient
import logging
from info import DATABASE_URI, DATABASE_NAME

# Initialize Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# MongoDB Client
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
collection = db["CONNECTION"]

async def add_connection(group_id, user_id):
    """Adds a new group connection for a user."""
    try:
        query = await collection.find_one({"_id": user_id}, {"_id": 0, "active_group": 0})

        if query:
            group_ids = {x["group_id"] for x in query.get("group_details", [])}
            if group_id in group_ids:
                return False  # Group already exists for user

        group_details = {"group_id": group_id}

        if not query:
            # If user does not exist, insert new document
            await collection.insert_one({
                "_id": user_id,
                "group_details": [group_details],
                "active_group": group_id
            })
        else:
            # Update existing document
            await collection.update_one(
                {"_id": user_id},
                {"$push": {"group_details": group_details}, "$set": {"active_group": group_id}}
            )

        return True
    except Exception as e:
        logger.exception(f"Error in add_connection: {e}")
        return False

async def active_connection(user_id):
    """Returns the active group for a user."""
    try:
        query = await collection.find_one({"_id": user_id}, {"_id": 0, "group_details": 0})
        return int(query["active_group"]) if query and query["active_group"] is not None else None
    except Exception as e:
        logger.exception(f"Error in active_connection: {e}")
        return None

async def all_connections(user_id):
    """Returns all group connections for a user."""
    try:
        query = await collection.find_one({"_id": user_id}, {"_id": 0, "active_group": 0})
        return [x["group_id"] for x in query.get("group_details", [])] if query else None
    except Exception as e:
        logger.exception(f"Error in all_connections: {e}")
        return None

async def if_active(user_id, group_id):
    """Checks if a given group is the active connection for a user."""
    try:
        query = await collection.find_one({"_id": user_id}, {"_id": 0, "group_details": 0})
        return query and query.get("active_group") == group_id
    except Exception as e:
        logger.exception(f"Error in if_active: {e}")
        return False

async def make_active(user_id, group_id):
    """Sets a given group as active for a user."""
    try:
        update = await collection.update_one({"_id": user_id}, {"$set": {"active_group": group_id}})
        return update.modified_count > 0
    except Exception as e:
        logger.exception(f"Error in make_active: {e}")
        return False

async def make_inactive(user_id):
    """Sets a user's active group to None (inactive)."""
    try:
        update = await collection.update_one({"_id": user_id}, {"$set": {"active_group": None}})
        return update.modified_count > 0
    except Exception as e:
        logger.exception(f"Error in make_inactive: {e}")
        return False

async def delete_connection(user_id, group_id):
    """Deletes a group connection for a user."""
    try:
        update = await collection.update_one(
            {"_id": user_id},
            {"$pull": {"group_details": {"group_id": group_id}}}
        )
        if update.modified_count == 0:
            return False  # No changes made (group not found)

        # Fetch updated user data
        query = await collection.find_one({"_id": user_id}, {"_id": 0})

        if query and query.get("group_details"):
            # If active group is being deleted, set last group in list as active
            if query.get("active_group") == group_id:
                new_active_group = query["group_details"][-1]["group_id"]
                await collection.update_one({"_id": user_id}, {"$set": {"active_group": new_active_group}})
        else:
            # If no groups left, set active_group to None
            await collection.update_one({"_id": user_id}, {"$set": {"active_group": None}})

        return True
    except Exception as e:
        logger.exception(f"Error in delete_connection: {e}")
        return False
        
