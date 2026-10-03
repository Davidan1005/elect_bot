import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import change_date as chd

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
MY_ID = int(os.getenv("TELEGRAM_ID")) if os.getenv("TELEGRAM_ID") else None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me your SIWES letter chief")


async def downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document:
        return

    # Sanitize original file name to prevent path traversal attacks
    safe_file_name = os.path.basename(document.file_name or f"doc_{document.file_id}")

    folder = "letters"
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, safe_file_name)

    try:
        # Download file
        new_file = await document.get_file()
        await new_file.download_to_drive(file_path)

        # Process file without blocking the async event loop
        output = await asyncio.to_thread(chd.change_date, file_path=file_path)

        await update.message.reply_text(
            f"{safe_file_name} edited successfully. Sending it back..."
        )

        output_path = os.path.abspath(output)

        # Send back to user
        with open(output_path, "rb") as doc:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=doc,
                filename=safe_file_name,
            )

        # Copy to admin channel/chat if set
        if MY_ID:
            with open(output_path, "rb") as doc:
                await context.bot.send_document(
                    chat_id=MY_ID,
                    document=doc,
                    filename=safe_file_name,
                )

    except Exception as e:
        logging.error(f"Failed to process document: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while processing your letter.")

    finally:
        # Cleanup temporary files
        if os.path.exists(file_path):
            os.remove(file_path)


def main():
    if not API_TOKEN:
        raise ValueError("API_TOKEN is missing from environment variables.")

    application = ApplicationBuilder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, downloader))

    webhook_url = os.environ.get("WEBHOOK_URL")
    port = int(os.environ.get("PORT", 10000))

    if webhook_url:
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
        )
    else:
        # Fallback to polling for local development
        application.run_polling()


if __name__ == "__main__":
    main()