import logging
import re
import base64
from struct import pack
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import (CAPTION_LANGUAGES, DATABASE_URI, DATABASE_URI2, DATABASE_NAME,
                  COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN,
                  DEENDAYAL_MOVIE_UPDATE_CHANNEL, OWNERID)
from utils import get_settings, save_group_settings, temp, get_movie_update_status
from database.users_chats_db import add_name
from .Imdbposter import get_movie_details, fetch_image
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Logger Setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize Databases
client1 = AsyncIOMotorClient(DATABASE_URI)
db1 = client1[DATABASE_NAME]
instance1 = Instance.from_db(db1)

client2 = AsyncIOMotorClient(DATABASE_URI2)
db2 = client2[DATABASE_NAME]
instance2 = Instance.from_db(db2)

@instance1.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

@instance2.register
class Media2(Media):
    pass  # Inherits everything from Media

# Choose Active Database
def choose_media_db():
    return Media if temp.get('indexDB') == DATABASE_URI else Media2

async def save_file(bot, media):
    """ Save file in database, avoiding duplicates """
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r'[_\-\.\+]', ' ', str(media.file_name))
    saveMedia = choose_media_db()
    
    try:
        if await saveMedia.count_documents({'file_id': file_id}, limit=1):
            logger.warning(f'{media.file_name} is already saved!')
            return False, 0
        
        file = saveMedia(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
        await file.commit()
        logger.info(f'{file_name} saved to database')

        if await get_movie_update_status(bot.me.id):
            await send_msg(bot, file.file_name, file.caption)
        
        return True, 1
    except (ValidationError, DuplicateKeyError):
        logger.exception("Error while saving file")
        return False, 2

async def send_msg(bot, filename, caption):
    """Send movie update messages to channel"""
    try:
        filename = re.sub(r'\(@\S+\)|\[\@\S+\]|\b@\S+', '', filename).strip()
        caption = re.sub(r'\(@\S+\)|\[\@\S+\]|\b@\S+', '', caption).strip()

        year_match = re.search(r"\b(19|20)\d{2}\b", caption)
        year = year_match.group(0) if year_match else None

        qualities = ["ORG", "hdcam", "HDRip", "camrip", "HDTC", "HDTS"]
        quality = await get_qualities(caption.lower(), qualities) or "HDRip"

        language = next((lang for lang in CAPTION_LANGUAGES if lang.lower() in caption.lower()), "Unknown")

        text = f"#New_File_Added ✅\n\n👷Name: `{filename}`\n\n🌳Quality: {quality}\n\n🍁Audio: {language}"
        if await add_name(OWNERID, filename):
            imdb = await get_movie_details(filename)
            resized_poster = await fetch_image(imdb.get('poster_url')) if imdb else None
            btn = [[InlineKeyboardButton('🌲 Get Files 🌲', url=f"https://t.me/{temp.U_NAME}?start=getfile-{filename.replace(' ', '-')}")]]
            
            if resized_poster:
                await bot.send_photo(DEENDAYAL_MOVIE_UPDATE_CHANNEL, resized_poster, caption=text, reply_markup=InlineKeyboardMarkup(btn))
            else:
                await bot.send_message(DEENDAYAL_MOVIE_UPDATE_CHANNEL, text, reply_markup=InlineKeyboardMarkup(btn))
    except Exception:
        logger.exception("Error sending message")

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0):
    """Search files in database"""
    query = query.strip()
    raw_pattern = query.replace(' ', r'.*[\s\.\+\-_()]') if ' ' in query else r'(|[\.\+\-_])' + query + r'(|[\.\+\-_])'
    regex = re.compile(raw_pattern, flags=re.IGNORECASE)

    filter = {'file_name': regex} if not USE_CAPTION_FILTER else {'$or': [{'file_name': regex}, {'caption': regex}]}
    if file_type:
        filter['file_type'] = file_type

    total_results = (await Media.count_documents(filter)) + (await Media2.count_documents(filter))
    cursor = Media.find(filter).sort('$natural', -1).skip(offset).limit(max_results)
    cursor2 = Media2.find(filter).sort('$natural', -1).skip(offset).limit(max_results)

    fileList = await cursor.to_list(length=max_results) + await cursor2.to_list(length=max_results)
    next_offset = offset + len(fileList) if len(fileList) == max_results else ''

    return fileList, next_offset, total_results

# Utility functions
def encode_file_id(s: bytes) -> str:
    return base64.urlsafe_b64encode(s + b'\x16' + b'\x04').decode().rstrip("=")

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(pack("<iiqq", int(decoded.file_type), decoded.dc_id, decoded.media_id, decoded.access_hash))
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref
