import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
MY_ID = os.getenv("TELEGRAM_ID")

# Folder containing the letters
LETTERS_FOLDER = Path("letters")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# ============================================================
# MATRIC NUMBER NORMALIZATION
# ============================================================

def normalize_matric(matric: str) -> str:
    """
    Normalize a matric number.

    Examples:

        23/1234
        23-1234
        23 1234

    All become:

        23/1234

    The /300 suffix is NOT required from the student.
    """

    matric = matric.strip()

    # Convert separators to /
    matric = re.sub(
        r"[\s\-_]+",
        "/",
        matric
    )

    # Remove /300 if someone happens to enter it
    matric = re.sub(
        r"/300$",
        "",
        matric,
        flags=re.IGNORECASE
    )

    # Normalize case
    matric = matric.title()

    return matric


# ============================================================
# FIND LETTER
# ============================================================

def find_letter(matric_number: str):
    """
    Find a letter based on matric number.

    Stored files are expected to look like:

        David Nduka - 23_1234_300.docx

    The student's input:

        23/1234

    will match that file.
    """

    normalized_matric = normalize_matric(
        matric_number
    )

    # Convert matric to the format used in filenames
    filename_matric = normalized_matric.replace(
        "/",
        "_"
    )

    # Search for:
    # 23_1234_300
    search_pattern = re.compile(
        rf"{re.escape(filename_matric)}_300(?:\.docx)?$",
        re.IGNORECASE
    )

    if not LETTERS_FOLDER.exists():
        return None

    for file in LETTERS_FOLDER.glob("*.docx"):

        if search_pattern.search(file.name):
            return file

    return None


# ============================================================
# START COMMAND
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "Send your matriculation number to receive "
        "your SIWES letter.\n\n"
        "Example:\n"
        "23/1234"
    )


# ============================================================
# MATRIC NUMBER HANDLER
# ============================================================

async def matric_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    matric_number = update.message.text.strip()

    logging.info(
        f"Matric number received: {matric_number}"
    )

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    normalized_matric = normalize_matric(
        matric_number
    )

    logging.info(
        f"Normalized matric number: "
        f"{normalized_matric}"
    )

    # --------------------------------------------------------
    # FIND LETTER
    # --------------------------------------------------------

    letter = find_letter(
        normalized_matric
    )

    # --------------------------------------------------------
    # NOT FOUND
    # --------------------------------------------------------

    if letter is None:

        await update.message.reply_text(
            f"I couldn't find a letter for "
            f"{normalized_matric}.\n\n"
            "Please check your matriculation number "
            "and try again."
        )

        logging.warning(
            f"No letter found for "
            f"{normalized_matric}"
        )

        return

    # --------------------------------------------------------
    # FOUND
    # --------------------------------------------------------

    logging.info(
        f"Found letter: {letter.name}"
    )

    await update.message.reply_text(
        "Found your letter. Sending it now..."
    )

    # --------------------------------------------------------
    # SEND TO STUDENT
    # --------------------------------------------------------

    with open(letter, "rb") as document:

        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=document,
            filename=letter.name,
        )

    logging.info(
        f"Sent {letter.name} to "
        f"user {update.effective_user.id}"
    )

    # --------------------------------------------------------
    # OPTIONAL ADMIN COPY
    # --------------------------------------------------------

    if MY_ID:

        with open(letter, "rb") as document:

            await context.bot.send_document(
                chat_id=MY_ID,
                document=document,
                filename=letter.name,
            )


# ============================================================
# MAIN
# ============================================================

def main():

    application = (
        ApplicationBuilder()
        .token(API_TOKEN)
        .build()
    )

    # /start
    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Matric number messages
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            matric_handler
        )
    )

    # --------------------------------------------------------
    # WEBHOOK
    # --------------------------------------------------------

    application.run_webhook(
        listen="0.0.0.0",
        port=int(
            os.environ.get("PORT", 10000)
        ),
        webhook_url=os.environ.get(
            "WEBHOOK_URL"
        ),
    )


if __name__ == "__main__":
    main()