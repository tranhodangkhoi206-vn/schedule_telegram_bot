import os
from dotenv import load_dotenv
import telebot
from telebot import types
from message import *
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import time

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


load_dotenv()


TOKEN = os.getenv("BOT_TOKEN") or ""

user_messages = {}

bot = telebot.TeleBot(token=TOKEN)

schedule_today = get_schedule_daily()


def delete_old_messages(user_id, minutes=5):
    """Xóa tin nhắn cũ hơn X phút"""

    if user_id not in user_messages:
        return

    current_time = time.time()
    time_threshold = minutes * 60  # Convert minutes to seconds

    # Lọc tin nhắn cần xóa
    to_delete = []
    to_keep = []

    for msg_data in user_messages[user_id]:
        elapsed_time = current_time - msg_data["timestamp"]

        if elapsed_time > time_threshold:
            # ★ Cũ hơn X phút -> xóa
            to_delete.append(msg_data)
        else:
            # ★ Mới hơn X phút -> giữ
            to_keep.append(msg_data)

    # Xóa tin nhắn
    for msg_data in to_delete:
        try:
            bot.delete_message(user_id, msg_data["msg_id"])
            print(f"✓ Xóa tin {msg_data['msg_id']}")
        except Exception as e:
            print(f"✗ Lỗi xóa: {e}")

    # Cập nhật danh sách
    user_messages[user_id] = to_keep


@bot.message_handler(commands=["start"])
def start(message):

    chat_id = message.chat.id

    logger.info(f"User {chat_id} gọi /start")

    delete_old_messages(chat_id, minutes=5)

    markup = types.InlineKeyboardMarkup()

    btn_schedule_today = types.InlineKeyboardButton(
        "Lấy lịch học hôm nay", callback_data="schedule_today"
    )
    markup.add(btn_schedule_today)
    sent = bot.send_message(
        chat_id,
        "Chào bạn tôi là bot lịch học của bạn đây!\n\n",
        reply_markup=markup,
    )
    # ★ Lưu: (message_id, thời điểm)
    if chat_id not in user_messages:
        user_messages[chat_id] = []

    user_messages[chat_id].append(
        {
            "msg_id": sent.message_id,
            "timestamp": time.time(),
        }  # ← Lưu thời gian hiện tại
    )


@bot.callback_query_handler(func=lambda call: True)
def handle_choice(call):
    if call.data == "schedule_today":
        logger.info(f"Gọi lấy lịch học")
        bot.send_message(call.message.chat.id, schedule_today)
        bot.answer_callback_query(call.id)


def startBot():
    logger.info("Bot đang khởi động")
    bot.infinity_polling()
