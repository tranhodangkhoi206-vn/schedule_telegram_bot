import os
import threading
import time
import traceback
from datetime import timedelta, datetime
from flask import Flask, request
from dotenv import load_dotenv
from telebot import types, TeleBot
from message import get_schedule_daily
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

# Tạo bot
TOKEN = os.getenv("BOT_TOKEN") or ""
bot = TeleBot(token=TOKEN)

# Khởi tạo webhook
app = Flask(__name__)

# Tạo lặp lại mỗi ngày
scheduler = BackgroundScheduler()
scheduler.start()
daily_job = {}

# Lưu các tin nhắn đã gửi
sent_messages = []
sent_command = {}


# Lệnh /start
@bot.message_handler(commands=["start"])
def start(message):
    try:
        chat_id = message.chat.id
        if chat_id in sent_command:
            bot.delete_message(chat_id, sent_command[chat_id])
        sent_command[chat_id] = message.message_id
        markup = types.InlineKeyboardMarkup()

        btn_schedule_today = types.InlineKeyboardButton(
            "Lấy lịch học hôm nay", callback_data="schedule_today"
        )
        btn_start_schedule_daily = types.InlineKeyboardButton(
            "Bật tính năng tự động gửi lịch", callback_data="start_schedule_daily"
        )
        btn_stop_schedule_daily = types.InlineKeyboardButton(
            "Tắt tính năng tự động gửi lịch", callback_data="stop_schedule_daily"
        )
        btn_clear_messages = types.InlineKeyboardButton(
            "Xóa tin nhắn", callback_data="clear_messages"
        )
        markup.add(
            btn_schedule_today,
        )
        markup.add(
            btn_start_schedule_daily,
            btn_stop_schedule_daily,
        )
        markup.add(
            btn_clear_messages,
        )
        msg = bot.send_message(
            chat_id,
            "Chào bạn tôi là bot lịch học của bạn đây!\n\n",
            reply_markup=markup,
        )
        sent_messages.append(msg.message_id)
    except Exception as ex:
        traceback.print_exception(ex)


# Thực thi lệnh /start
@bot.callback_query_handler(func=lambda call: call.data == "schedule_today")
def handle_choice(call):
    msg = bot.send_message(call.message.chat.id, get_schedule_daily())
    bot.answer_callback_query(call.id)
    sent_messages.append(msg.message_id)


# Tạo log đếm ngược thời gian
def time_countdown(target_time, chat_id):
    while True:
        remain_time = int((target_time - datetime.now()).total_seconds())

        if remain_time <= 0:
            bot.send_message(chat_id, "0")
            break

        bot.send_message(chat_id, f"{remain_time}")
        time.sleep(1)


# Chạy và gửi nội dung sau một thời gian
def run_daily(chat_id):
    msg = bot.send_message(chat_id, get_schedule_daily())
    sent_messages.append(msg.message_id)


# Hàm call back bắt đàu chức năng lịch mỗi ngày
@bot.callback_query_handler(func=lambda call: call.data == "start_schedule_daily")
def start_daily_schedule(call):
    global msg
    chat_id = call.message.chat.id
    try:
        if chat_id in daily_job:
            msg = bot.send_message(chat_id, "Tính năng tự động đã được bật")
            return
        job = scheduler.add_job(
            func=run_daily,
            args=[chat_id],
            trigger="cron",
            hour=6,
        )
        daily_job[chat_id] = job
        msg = bot.send_message(chat_id, "Đã khởi động tính năng gửi lịch tự động!")
        sent_messages.append(msg.message_id)
        bot.answer_callback_query(call.id)
    except Exception as ex:
        traceback.print_exc()


# Hàm call back dừng chức năng lịch mỗi ngày
@bot.callback_query_handler(func=lambda call: call.data == "stop_schedule_daily")
def stop_daily_schedule(call):
    chat_id = call.message.chat.id
    if chat_id in daily_job:
        # Xóa phiên làm việc của scheduler bằng remove()
        daily_job[chat_id].remove()
        # Xóa giá trị job được lưu trong daily_jobs
        del daily_job[chat_id]
        msg = bot.send_message(chat_id, "Đã dừng tính năng gửi lịch tự động")
        sent_messages.append(msg.message_id)
        bot.answer_callback_query(call.id)
    else:
        msg = bot.send_message(chat_id, "Bạn chưa bật tính năng này!")
        sent_messages.append(msg.message_id)


# Nhận về tất cả tin nhắn và xóa toàn bộ
@bot.callback_query_handler(func=lambda call: call.data == "clear_messages")
def delete_history(call):
    chat_id = call.message.chat.id
    for message_id in sent_messages:
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    sent_messages.clear()
    bot.answer_callback_query(call.id)


# Chạy bot bằng webhook
@app.route(f"/webhook", methods=["POST"])
def webhook():
    update = types.Update.de_json(request.get_data(as_text=True))
    if isinstance(update, types.Update):
        bot.process_new_updates([update])
    return "OK", 200


def start_bot():
    bot.remove_webhook()
    bot.set_webhook(url="https://cannon-uncurious-yearly.ngrok-free.dev/webhook")
    app.run(host="0.0.0.0", port=8080, use_reloader=True)
