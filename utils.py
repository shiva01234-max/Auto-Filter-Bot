import logging
from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import LONG_IMDB_DESCRIPTION, ADMINS, IS_PREMIUM, TIME_ZONE, USE_CAPTION_FILTER, UPDATES_SEND_CHANNEL, FILMS_LINK
from database.users_chats_db import db
import re
import os
import sys
import time
from datetime import datetime
import asyncio
from shortzy import Shortzy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CURRENT = None
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None

async def is_subscribed(bot, query):
    if not UPDATES_SEND_CHANNEL:
        return True
    try:
        user = await bot.get_chat_member(UPDATES_SEND_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        return False
    except Exception as e:
        logger.exception(e)
        return False
    return True

def get_size(size):
    """Get size in readable format"""
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{round(size, 2)} {units[i]}"

def get_plan_name(user_id):
    return "Premium" if IS_PREMIUM else "Free"

def handle_next_back(query, current_page, total_pages):
    buttons = []
    if current_page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"next_{current_page - 1}"))
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"next_{current_page + 1}"))
    return buttons

async def send_update(bot, message, text, reply_markup=None):
    try:
        await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in send_update: {e}")
