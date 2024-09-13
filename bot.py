from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
import logging
import requests
import json
import motivator
import mergeaudio
import os
import subprocess
import worker

logger = logging.getLogger(__name__)

telegram_bot_key = os.getenv('TELEGRAM_BOT_TOKEN')


def start(update: Update, context: CallbackContext) -> None:
    #update.message.reply_text('Hello! Welcome to the bot.')
    context.bot.send_audio(update.message.chat_id, audio=open("audio/WelcomeTutorial.mp3", 'rb'))


# Convert ogg file to mp3 file
def convert_ogg_to_mp3(ogg_file_path, mp3_file_path, overwrite=True):
    command = [
        'ffmpeg',
        '-y' if overwrite else '-n',  # Overwrite file if it exists (-y) or do not overwrite (-n)
        '-i', ogg_file_path,  # Input file
        '-codec:a', 'libmp3lame',  # Use mp3 codec
        '-q:a', '2',  # Set the quality of the mp3
        mp3_file_path  # Output file
    ]

    subprocess.run(command, check=True)


def arni(update: Update, context: CallbackContext) -> None:
    # Find out the name of the person who sent the message
    sender_name = update.message['chat']['first_name']

    # Print the message in the terminal to know what's going on
    print(f'{update.message.from_user.first_name} wrote {update.message.text}')

    # Send a message into the persons telegram chat, so they know the script is working
    context.bot.send_message(update.message.chat_id,
                             f"Alright, let me do my magic...")

    if not update.message.voice.file_id:
        context.bot.send_message(update.message.chat_id,
                                 f"Please send me your instructions in an audio message.")

    if update.message.voice.file_id:
        # Get the ID of the instructions, which are inside an audio file
        instruction_audio_id = update.message.voice.file_id

        # Request the URL to download the instruction audio to be able to download the file
        instruction_audio_url = requests.get(
            f"https://api.telegram.org/bot{telegram_bot_key}/getFile?file_id={instruction_audio_id}")
        instruction_audio_url = instruction_audio_url.content.decode('utf-8')
        instruction_audio_url = json.loads(instruction_audio_url)['result']['file_path']

        # Download the instruction audio and get the content
        instruction_audio = requests.get(
            f"https://api.telegram.org/file/bot{telegram_bot_key}/{instruction_audio_url}")
        instruction_audio = instruction_audio.content

        # Save the instruction audio as ogg file
        with open(f"audio/instruction_audio.ogg", "wb") as f:
            f.write(instruction_audio)

        # Convert ogg file to mp3 file
        convert_ogg_to_mp3(f"audio/instruction_audio.ogg", f"audio/instruction_audio.mp3")
        print("Converted successfully.")

        # Use OpenAI's Whisper to transcribe the instruction audio
        transcript = motivator.transcribe("instruction_audio.mp3")

        # Use OpenAI to write a motivation as Arndold Schwarzenegger
        motivation = arnold.motivate(transcript)

        # Use Elevenlabs to read the motivation into audio file with Arnold Schwarzenegger's voice
        arnold.talk(motivation)

        motivator.merge_audio_files_with_delay('audio/ArniVoice.mp3', 'audio/ArniBackground_Small.mp3', 'audio/arnold.mp3', 5)

        # Send motivation text and audio into telegram chat
        context.bot.send_message(update.message.chat_id, f"{motivation}")
        context.bot.send_audio(update.message.chat_id, audio=open("audio/arnold.mp3", 'rb'))


def main() -> None:
    updater = Updater(telegram_bot_key)

    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher

    # on /start command send a welcome message
    dispatcher.add_handler(CommandHandler("start", start))

    # Have arnold react on messages send to bot
    dispatcher.add_handler(MessageHandler(~Filters.command, arni))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
