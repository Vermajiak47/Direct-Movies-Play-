from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME
from pyrogram import enums
import logging

# Setup Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Initialize MongoDB Client
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]

async def add_filter(grp_id, text, reply_text, btn, file, alert):
    """Adds or updates a filter in the database for a specific group."""
    collection = db[str(grp_id)]
    data = {
        'text': str(text),
        'reply': str(reply_text),
        'btn': str(btn),
        'file': str(file),
        'alert': str(alert)
    }
    try:
        await collection.update_one({'text': str(text)}, {"$set": data}, upsert=True)
    except Exception as e:
        logger.exception(f"Error in add_filter: {e}")

async def find_filter(group_id, name):
    """Finds a filter by text in a specific group."""
    collection = db[str(group_id)]
    try:
        file = await collection.find_one({"text": name})
        if file:
            return file.get('reply'), file.get('btn'), file.get('alert', None), file.get('file')
        return None, None, None, None
    except Exception as e:
        logger.exception(f"Error in find_filter: {e}")
        return None, None, None, None

async def get_filters(group_id):
    """Returns a list of all filter texts in a specific group."""
    collection = db[str(group_id)]
    try:
        texts = [doc['text'] async for doc in collection.find({}, {'text': 1})]
        return texts
    except Exception as e:
        logger.exception(f"Error in get_filters: {e}")
        return []

async def delete_filter(message, text, group_id):
    """Deletes a specific filter in a group."""
    collection = db[str(group_id)]
    query = {"text": text}

    try:
        result = await collection.delete_one(query)
        if result.deleted_count > 0:
            await message.reply_text(
                f"'`{text}`' deleted. I'll not respond to that filter anymore.",
                quote=True,
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await message.reply_text("Couldn't find that filter!", quote=True)
    except Exception as e:
        logger.exception(f"Error in delete_filter: {e}")

async def del_all(message, group_id, title):
    """Deletes all filters in a specific group."""
    collection_name = str(group_id)

    if collection_name not in await db.list_collection_names():
        await message.edit_text(f"Nothing to remove in {title}!")
        return

    try:
        await db.drop_collection(collection_name)
        await message.edit_text(f"All filters from {title} have been removed")
    except Exception as e:
        logger.exception(f"Error in del_all: {e}")
        await message.edit_text("Couldn't remove all filters from group!")

async def count_filters(group_id):
    """Returns the count of filters in a specific group."""
    collection = db[str(group_id)]
    try:
        count = await collection.count_documents({})
        return count if count > 0 else False
    except Exception as e:
        logger.exception(f"Error in count_filters: {e}")
        return False

async def filter_stats():
    """Returns the total number of collections (groups) and filters."""
    try:
        collections = await db.list_collection_names()
        if "CONNECTION" in collections:
            collections.remove("CONNECTION")

        total_filters = 0
        for collection in collections:
            col = db[collection]
            total_filters += await col.count_documents({})

        return len(collections), total_filters
    except Exception as e:
        logger.exception(f"Error in filter_stats: {e}")
        return 0, 0
        
