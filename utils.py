import os
import re
import base64
import re
from pyrogram import enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from database.users_chats_db import db
from info import ADMINS, UPDATES_SEND_CHANNEL, FILMS_LINK, IS_PREMIUM, LONG_IMDB_DESCRIPTION
from utils import script

class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CURRENT = int(os.environ.get("SKIP_FILMS", 0))
    CANCEL = False
    VERIFICATIONS = {}
    BOT = None
    PREMIUM_USERS = []

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{round(size, 2)} {units[i]}"

def split_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

async def send_update(title, year):
    if not UPDATES_SEND_CHANNEL:
        return
    btn = [[InlineKeyboardButton('📥 Request from Here 📥', url=FILMS_LINK)]]
    
    # TMDB bypass, direct default dictionary data milega
    data = await get_poster(f"{title} {year}")
    
    _year = f"({year})" if year else ""
    caption = script.NEW_ADDED_TEMPLATE.format(
        title=data['title'],
        kind=data['kind'],
        votes=data['votes'],
        tmdb_id=data["tmdb_id"],
        runtime=data["runtime"],
        release_date=data['release_date'],
        year=data['year'],
        genres=data['genres'],
        plot=data['plot'],
        rating=data['rating'],
        url=data['url'],
        languages=data['languages'],
        countries=data['countries']
    )
    
    await temp.BOT.send_message(
        chat_id=UPDATES_SEND_CHANNEL,
        text=caption,
        reply_markup=InlineKeyboardMarkup(btn)
    )
    return

async def get_poster(query, bulk=False, id=False, file=None):
    # TMDB disable karke direct template response return karne ke liye
    return {
        'title': query.title(),
        'kind': 'movie',
        'votes': 'N/A',
        'tmdb_id': 0,
        'runtime': 'N/A',
        'release_date': 'N/A',
        'year': 'N/A',
        'genres': 'N/A',
        'plot': 'No description available (TMDB Disabled).',
        'rating': 0,
        'url': 'https://imdb.com',
        'languages': 'Hindi/English',
        'countries': 'India'
    }

async def is_check_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False

async def get_verify_status(user_id):
    verify = temp.VERIFICATIONS.get(user_id)
    if not verify:
        verify = await db.get_verify_status(user_id)
        temp.VERIFICATIONS[user_id] = verify
    return verify

async def update_verify_status(user_id, verify_token="", is_verified=False, link="", expire_time=0):
    current = await get_verify_status(user_id)
    current['verify_token'] = verify_token
    current['is_verified'] = is_verified
    current['link'] = link
    current['expire_time'] = expire_time
    temp.VERIFICATIONS[user_id] = current
    await db.update_verify_status(user_id, current)

async def is_premium(user_id, bot):
    if not IS_PREMIUM:
        return True
    if user_id in ADMINS:
        return True
    mp = await db.get_plan(user_id)
    if mp['premium']:
        if mp['expire'] < datetime.now():
            await bot.send_message(user_id, f"Your premium {mp['plan']} is expired in {mp['expire'].strftime('%Y.%m.%d %H:%M:%S')}, use /plan to activate new plan again")
            mp['expire'] = ''
            mp['plan'] = ''
            mp['premium'] = False
            await db.update_plan(user_id, mp)
            return False
        return True
    else:
        return False

async def check_premium(bot):
    while True:
        pr = [i for i in await db.get_premium_users() if i['status']['premium']]
        for p in pr:
            mp = p['status']
            if mp['expire'] < datetime.now():
                try:
                    await bot.send_message(p['id'], f"Your premium {mp['plan']} is expired in {mp['expire'].strftime('%Y.%m.%d %H:%M:%S')}, use /plan to activate new plan again")
                except Exception:
                    pass
