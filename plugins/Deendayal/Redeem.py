from datetime import datetime, timedelta
import pytz
import string
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from info import ADMINS, PREMIUM_LOGS
from utils import get_seconds, temp

class RedeemDB:
    def __init__(self, db):
        self.collection = db.redeem_codes  # Store codes persistently

    async def add_code(self, code, duration):
        await self.collection.insert_one({"code": code, "duration": duration})

    async def get_code(self, code):
        return await self.collection.find_one({"code": code})

    async def remove_code(self, code):
        await self.collection.delete_one({"code": code})

redeem_db = RedeemDB(db)

def generate_code(length=10):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))

@Client.on_message(filters.command("add_redeem") & filters.user(ADMINS))
async def add_redeem_code(client, message):
    if len(message.command) != 3:
        return await message.reply_text("<b>♻ Usage:\n\n➩ <code>/add_redeem 1min 1</code>\n➩ <code>/add_redeem 1hour 10</code>\n➩ <code>/add_redeem 1day 5</code></b>")

    try:
        time = message.command[1]
        num_codes = int(message.command[2])
    except ValueError:
        return await message.reply_text("❌ Please provide a valid number.")

    codes = []
    for _ in range(num_codes):
        code = generate_code()
        await redeem_db.add_code(code, time)  # Store in DB
        codes.append(code)

    codes_text = '\n'.join(f"➔ <code>/redeem {code}</code>" for code in codes)
    text = f"""
<b>🎉 <u>Gift Code Generated ✅</u></b>

<b> <u>Total Codes:</u></b> {num_codes}

{codes_text}

<b>⏳ <u>Duration:</u></b> {time}

🌟<u>𝗥𝗲𝗱𝗲𝗲𝗺 𝗖𝗼𝗱𝗲 𝗜𝗻𝘀𝘁𝗿𝘂𝗰𝘁𝗶𝗼𝗻</u>🌟

<b>Click on the code above to copy it instantly!</b>
<b>Send the copied code to the bot</b>\n to unlock your premium features!

<b>🚀 Enjoy your premium access! 🔥</b>
"""

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔑 Redeem Now 🔥", url=f"https://t.me/{temp.U_NAME}")]]
    )

    await message.reply_text(text, reply_markup=keyboard)


@Client.on_message(filters.command("redeem"))
async def redeem_code(client, message):
    if len(message.command) != 2:
        return await message.reply_text("Usage: /redeem <code>")

    redeem_code = message.command[1]
    code_data = await redeem_db.get_code(redeem_code)

    if not code_data:
        return await message.reply_text("❌ Invalid Redeem Code or Expired.")

    try:
        time = code_data["duration"]
        seconds = await get_seconds(time)
        if seconds <= 0:
            return await message.reply_text("❌ Invalid time format in redeem code.")

        user_id = message.from_user.id
        user = await client.get_users(user_id)
        now_aware = datetime.now(pytz.utc)

        # Fetch user data
        data = await db.get_user(user_id)
        current_expiry = data.get("expiry_time") if data else None

        if current_expiry:
            current_expiry = current_expiry.replace(tzinfo=pytz.utc)

        if current_expiry and current_expiry > now_aware:
            expiry_str = current_expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p")
            return await message.reply_text(
                f"🚫 <b>You already have active premium access!</b>\n\n"
                f"⏳ <b>Current Expiry:</b> {expiry_str}\n\n"
                f"<i>You cannot redeem another code until your current premium access expires.</i>\n\n"
                f"<b>Thank you for using our service! 🔥</b>",
                disable_web_page_preview=True
            )

        # Update premium expiry
        expiry_time = now_aware + timedelta(seconds=seconds)
        await db.update_user({"id": user_id, "expiry_time": expiry_time})
        await redeem_db.remove_code(redeem_code)  # Delete redeemed code

        expiry_str = expiry_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p")
        await message.reply_text(
            f"🎉 <b>Premium activated successfully! 🚀</b>\n\n"
            f"👤 <b>User:</b> {user.mention}\n"
            f"⚡ <b>User ID:</b> <code>{user_id}</code>\n"
            f"⏳ <b>Premium Duration:</b> <code>{time}</code>\n"
            f"⌛️ <b>Expiry Date:</b> {expiry_str}",
            disable_web_page_preview=True
        )

        # Log the redemption
        log_message = f"""
#Redeem_Premium 🔓

👤 <b>User:</b> {user.mention}
⚡ <b>User ID:</b> <code>{user_id}</code>
⏳ <b>Premium Duration:</b> <code>{time}</code>
⌛️ <b>Expiry Date:</b> {expiry_str}

🎉 Premium activated successfully! 🚀
"""
        await client.send_message(PREMIUM_LOGS, text=log_message, disable_web_page_preview=True)

    except Exception as e:
        await message.reply_text(f"⚠ An error occurred: {e}")
     
