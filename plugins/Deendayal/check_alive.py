import time
import asyncio
import platform
import os
import shutil
from pyrogram import Client, filters

CMD = ["/", "."]  

@Client.on_message(filters.command("alive", CMD))
async def check_alive(_, message):
    try:
        sticker = await message.reply_sticker("CAACAgIAAxkBAAEBVAlmCYqbLub_o5pVUOEwbqhV8kRytgACRBkAAgjh2UlSqev16oISqB4E") 
        text = await message.reply_text("Yᴏᴜ ᴀʀᴇ ᴠᴇʀʏ ʟᴜᴄᴋʏ 🤞 I ᴀᴍ ᴀʟɪᴠᴇ ❤️\nPʀᴇss /start ᴛᴏ ᴜsᴇ ᴍᴇ!")
        await asyncio.sleep(60)
        await sticker.delete()
        await text.delete()
        await message.delete()
    except Exception as e:
        print(f"Error in /alive: {e}")

@Client.on_message(filters.command("ping", CMD))
async def ping(_, message):
    start_t = time.perf_counter()
    try:
        rm = await message.reply_text("🏓 Pinging...")
        end_t = time.perf_counter()
        time_taken_s = (end_t - start_t) * 1000
        await rm.edit(f"🏓 Pong! **{time_taken_s:.3f} ms**")
        await asyncio.sleep(60)
        await rm.delete()
        await message.delete()
    except Exception as e:
        print(f"Error in /ping: {e}")

start_time = time.time()

def format_time(seconds):
    """Convert seconds to H:M:S format."""
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {sec}s"

def get_size(size_kb):
    """Convert KB to a human-readable format."""
    size_bytes = int(size_kb) * 1024
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def get_system_info():
    bot_uptime = format_time(time.time() - start_time)
    os_info = platform.system()

    system_uptime = "Unavailable"
    total_ram, used_ram, total_disk, used_disk = "Unavailable", "Unavailable", "Unavailable", "Unavailable"

    if os_info == "Linux":
        try:
            with open('/proc/uptime') as f:
                system_uptime = format_time(float(f.readline().split()[0]))
        except Exception:
            pass
        try:
            with open('/proc/meminfo') as f:
                meminfo = f.readlines()
            total_ram = get_size(meminfo[0].split()[1])  
            available_ram = get_size(meminfo[2].split()[1])  
            used_ram = get_size(int(meminfo[0].split()[1]) - int(meminfo[2].split()[1]))
        except Exception:
            pass
        try:
            total_disk, used_disk, _ = shutil.disk_usage("/")
            total_disk = get_size(total_disk // 1024)
            used_disk = get_size(used_disk // 1024)
        except Exception:
            pass

    return (
        f"💻 **System Information**\n\n"
        f"🖥️ **OS:** {os_info}\n"
        f"⏰ **Bot Uptime:** {bot_uptime}\n"
        f"🔄 **System Uptime:** {system_uptime}\n"
        f"💾 **RAM Usage:** {used_ram} / {total_ram}\n"
        f"📁 **Disk Usage:** {used_disk} / {total_disk}\n"
    )

async def calculate_latency():
    start = time.perf_counter()
    await asyncio.sleep(0)
    return f"{(time.perf_co
