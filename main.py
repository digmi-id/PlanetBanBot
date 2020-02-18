# -*- coding: utf-8 -*-

import sys
import logging
import traceback
from uuid import uuid4
from functools import wraps
from datetime import datetime, time

import pytz
from emoji import emojize
from telegram import InlineQueryResultArticle, InlineKeyboardButton, InlineKeyboardMarkup, InputTextMessageContent, ParseMode, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown

from config import Config


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Emoji
emo_heart_eyes = emojize(':heart_eyes:', use_aliases=True)
emo_wink = emojize(':wink:', use_aliases=True)
emo_book = emojize(':book:', use_aliases=True)
emo_hushed = emojize(':hushed:', use_aliases=True)
emo_persevere = emojize(':persevere:', use_aliases=True)
emo_sunglasses = emojize(':sunglasses:', use_aliases=True)
emo_question = emojize(':question:', use_aliases=True)
emo_start = emojize(':arrow_forward:', use_aliases=True)
emo_cry = emojize(':cry:', use_aliases=True)

# Passcode
passcode = 12345


def utc_to_wib(d: datetime) -> datetime:
    aware = pytz.utc.localize(d)
    return aware.astimezone(pytz.timezone("Asia/Jakarta"))


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context,  *args, **kwargs)
        return command_func

    return decorator


def cmd_start(update, context):
    """Send a message when the command /start is issued."""

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Halo salam kenal! Aku Bot dari Planet Ban {emo_heart_eyes}")


def cmd_help(update, context):
    """Send a message when the command /help is issued."""

    TEXT = f'''Hei, kamu butuh bantuan ya? {emo_hushed}, aku masih dikembangkan jadi maaf yaa kalo aku masih bingung. <br />Ini adalah perintah yang aku mengerti, silakan panggil aku dengan memberikan perintah dibawah ini yaaa {emo_wink}<br />
    /start - {emo_start} mulai dari sini yaaa kalo belum
    /help - {emo_question} butuh bantuan aku?
    /laporan - {emo_book} kamu mau melihat laporan?
    '''
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=TEXT)


def cmd_laporan(update, context):
    keyboard = [
        [
            InlineKeyboardButton("Karyawan", callback_data=f'Laporan Data Karyawan'),
            InlineKeyboardButton("Penjualan", callback_data=f'Laporan Data Penjualan')
        ],
        [
            InlineKeyboardButton("Kehadiran Karyawan", callback_data=f'Pendataan Kehadiran Karyawan')
        ],
    ]
    update.message.reply_text(
        'Silakan dipilih menunya yaa',
        reply_markup=InlineKeyboardMarkup(keyboard))


@send_action(ChatAction.UPLOAD_DOCUMENT)
def btn_laporan(update, context):
    query = update.callback_query
    query.edit_message_text(
        text=f"Bagus! kamu memilih <b>{query.data}</b> tapi maaf yaa ini baru dikembangkan {emo_wink} ini file yang kamu mau",
        parse_mode=ParseMode.HTML)
    context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open('laporan/contoh-laporan.pdf', 'rb'))


def cmd_hadir(update, context):
    opened, closed = time(9, 0, 0), time(21, 0, 0)
    msg_sent = update.message.date
    mention = mention_html(update.effective_user.id, update.effective_user.full_name)

    if not (utc_to_wib(msg_sent).time() >= opened) and (utc_to_wib(msg_sent).time() <= closed):
        text = f"Maaf {mention} kehadiran mu tidak dalam jam operasional toko!"
    else:
        if not context.args:
            text = f"{mention} passcode gak boleh kosong yaa!"
        else:
            if int(context.args[0]) == passcode:
                present = utc_to_wib(msg_sent).strftime('%m/%d/%Y, %H:%M:%S')
                text = f"Kehadiran {mention} berhasil di catat pada <code>{present}</code>"
            else:
                text = f"{mention} passcode kamu salah!"

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.HTML)


def unknown(update, context):
    """Send a message when the unknown command is issued."""

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Duh maaf!, aku gak ngerti yang kamu maksud {emo_persevere}")


def error(update, context):
    """Log Errors caused by Updates."""

    if update.effective_message:
        text = f"Hey. Maaf yaa ada kesalahan saat aku mencoba menangani pembaruan mu {emo_cry}," \
            f" tapi para developer ku lagi berusaha memperbaikinya {emo_wink}"
        update.effective_message.reply_text(text)

    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    payload = ""
    if update.effective_user:
        payload += f' with the user {mention_markdown(update.effective_user.id, update.effective_user.first_name)}'

    if update.effective_chat:
        payload += f' within the chat <i><u>{update.effective_chat.title}</u></i>'
        if update.effective_chat.username:
            payload += f' (@{update.effective_chat.username})'

    text = f"Hey.\nThe error <code>{context.error}</code> happened{payload}." \
        f" The full traceback:\n\n<code>{trace}</code>"
    for dev_id in Config.DEVELOPERS:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)

    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main(API_TOKEN):
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token=API_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # -------------------------------------------------------------------------
    # Register all your handler here!
    # -------------------------------------------------------------------------
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler('start', cmd_start))
    dp.add_handler(CommandHandler('help', cmd_help))
    dp.add_handler(CommandHandler('laporan', cmd_laporan))
    dp.add_handler(CommandHandler('hadir', cmd_hadir))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(CallbackQueryHandler(btn_laporan))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    # -------------------------------------------------------------------------

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main(Config.API_TOKEN)
