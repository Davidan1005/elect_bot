import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

# Folder containing the already-split SIWES letters
LETTERS_FOLDER = Path("letters")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def normalize_matric(matric: str) -> str:
    """
    Convert different ways of entering a matric number
    into one standard format.

    Examples:
        23/1234       -> 23/1234
        23-1234       -> 23/1234
        23 1234       -> 23/1234
        23/1234/300   -> 23/1234
    """

    matric = matric.strip()

    # Remove the /300 suffix if the student includes it
    matric = re.sub(r"[/\\\-_ ]*300$", "", matric, flags=re.IGNORECASE)

    # Convert spaces, dashes and backslashes to /
    matric = re.sub(r"[\s\-_\\]+", "/", matric)

    # Clean up repeated /
    matric = re.sub(r"/+", "/", matric)

    return matric.title()


def find_letter(matric_number: str):
    """
    Find the student's letter in the letters folder.
    """

    if not LETTERS_FOLDER.exists():
        logging.error("Letters folder does not exist.")
        return None

    normalized = normalize_matric(matric_number)

    # Convert:
    # 23/1234 -> 23_1234
    filename_matric = normalized.replace("/", "_")

    logging.info(f"Looking for matric number: {filename_matric}")

    for file in LETTERS_FOLDER.glob("*.docx"):

        # Example filename:
        # David Nduka - 23_1234_300.docx

        filename = file.stem.lower()

        expected = f"{filename_matric}_300".lower()

        if filename.endswith(expected):
            logging.info(f"Found letter: {file}")
            return file

    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message is None:
        return

    await update.message.reply_text(
        "Send your matriculation number.\n\n"
        "Example:\n"
        "23/1234"
    )


async def matric_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message is None:
        return

    if update.message.text is None:
        return

    matric_number = update.message.text.strip()

    if not matric_number:
        await update.message.reply_text(
            "Please send your matriculation number."
        )
        return

    logging.info(f"Student entered matric number: {matric_number}")

    letter = find_letter(matric_number)

    if letter is None:
        await update.message.reply_text(
            "I couldn't find a letter for that matric number.\n\n"
            "Please check the number and try again."
        )
        return

    await update.message.reply_text(
        "Found your SIWES letter. Sending it now..."
    )

    try:
        with open(letter, "rb") as document:

            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=document,
                filename=letter.name,
            )

        logging.info(
            f"Successfully sent {letter.name} "
            f"to {update.effective_chat.id}"
        )

    except Exception as e:

        logging.error(
            f"Failed to send letter: {e}",
            exc_info=True
        )

        await update.message.reply_text(
            "I found your letter, but I couldn't send it. "
            "Please try again."
        )


def main():

    if not API_TOKEN:
        raise ValueError(
            "API_TOKEN is missing from environment variables."
        )

    # Make sure the letters folder exists
    if not LETTERS_FOLDER.exists():
        raise FileNotFoundError(
            f"Letters folder not found: "
            f"{LETTERS_FOLDER.absolute()}"
        )

    application = (
        ApplicationBuilder()
        .token(API_TOKEN)
        .build()
    )

    # /start
    application.add_handler(
        CommandHandler("start", start)
    )

    # Normal text messages = matric numbers
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            matric_handler
        )
    )

    # LOCAL TESTING:
    # Use polling instead of webhook.
    application.run_polling()


if __name__ == "__main__":
    main()