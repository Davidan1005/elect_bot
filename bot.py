import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

import change_date as chd

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
MY_ID = os.getenv("TELEGRAM_ID")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me your SIWES letter chief"
    )


async def downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Get the uploaded file's name
    file_name = update.message.document.file_name

    # Get the Telegram file
    new_file = await update.message.document.get_file()

    # Temporary folder
    folder = "letters"
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, file_name)

    # Download
    await new_file.download_to_drive(file_path)

    # Edit
    output = chd.change_date(file_path=file_path)

    # Send edited file back
    await update.message.reply_text(
        f"{file_name} edited successfully. Sending it back..."
    )

    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=os.path.abspath(output),
    )
    await context.bot.send_document(
            chat_id=MY_ID,
            document=os.path.abspath(output),
        )



def main():

    application = ApplicationBuilder().token(API_TOKEN).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        MessageHandler(filters.Document.ALL, downloader)
    )

    # Start webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=os.environ.get("WEBHOOK_URL"),
    )


if __name__ == "__main__":
    main()