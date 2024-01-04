import subprocess
from elevenlabs import generate, set_api_key, Voice, VoiceSettings, generate
from openai import OpenAI
import os


def merge_audio_files_with_delay(first_file, second_file, output_file, delay):
    command = [
        'ffmpeg',
        '-y',  # Automatic overwrite flag
        '-i', first_file,
        '-i', second_file,
        '-filter_complex', f"[1:a]volume=0.7[volume_adjusted];[0:a][volume_adjusted]amix=inputs=2:duration=shortest",
        output_file
    ]
    subprocess.run(command)


# Set OpenAI Key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Set 11Labs Key
set_api_key(api_key=os.getenv('11LABS_API_KEY'))

# Set Voice ID
voice_id = os.getenv('11LABS_VOICE_ID')  # Replace with Arni


# Write motivational speech based on transcript instructions
def motivate(transcript):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": f"""
                You are Arnold Schwarzenegger. Take the following instructions and create a short motivational, inspiring speech: {transcript}
                Use up to 120 words, but not more.""",
            },
        ]
        ,
        max_tokens=500,
    )
    response_text = response.choices[0].message.content
    return response_text


# Read motivational speech into audio file
def talk(motivational_speech):
    audio = generate(
        text=motivational_speech,
        voice=Voice(
            voice_id=voice_id,
            settings=VoiceSettings(stability=0.75, similarity_boost=0.65, style=0.8, use_speaker_boost=True)
        )
    )

    with open("audio/ArniVoice.mp3", "wb") as f:
        f.write(audio)
    return True


def transcribe(file_name_mp3):
    audio_file = open(f"audio/{file_name_mp3}", "rb")

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

    result = transcript.text
    return result

