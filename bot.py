import logging
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler



from dotenv import  load_dotenv

import change_date as chd

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Send me your SIWES letter chief")

async def downloader(update, context):
    # Download file
    fileName = update.message.document.file_name
    new_file = await update.message.effective_attachment.get_file()

    folder = "letters"
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, fileName)


    await new_file.download_to_drive(file_path)

    output = chd.change_date(file_path=file_path)
    output_path = os.path.abspath(output)

    chat_id = update.message.chat.id

    # Acknowledge file received
    await update.message.reply_text(f"{fileName} saved successfully")

    await context.bot.send_document(
        chat_id=chat_id,
        document=output_path
    )




if __name__ == '__main__':
    application = ApplicationBuilder().token(API_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.add_handler(MessageHandler(filters.ALL, downloader))
    
    application.run_polling()