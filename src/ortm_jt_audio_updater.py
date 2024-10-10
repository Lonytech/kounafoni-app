import logging
from datetime import datetime
from pathlib import Path

from speech_to_text import TVNewsSpeechToText
from summarizer import Summarizer
from text_to_speech import NewsTextToSpeech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STT_PATH = Path(__file__).parents[1] / "data" / "whisper"
SUMMARIZED_TEXTS_PATH = STT_PATH / "summarized_texts"
JT_20H_PLAYLIST_URL = "https://youtube.com/playlist?list=PLDBQmURq6pOfBKc6WU0wXTg2vxAjxjQel&si=n9iNX7AUi-SpNN_N"


def get_most_recent_folder(directory_path):
    # Convert the input to a Path object if it's a string
    base_path = Path(directory_path)

    # Get all directories and filter those that match date format
    # Assuming folders are named in the format "YYYY-MM-DD"
    date_folders = []
    for folder in base_path.iterdir():
        if folder.is_dir():
            try:
                # Try to parse the folder name as a date
                date = datetime.strptime(folder.name, "%Y-%m-%d")
                date_folders.append((date, folder))
            except ValueError:
                # Skip folders that don't match the date format
                continue

    if not date_folders:
        return None

    # Sort by date and get the most recent one
    most_recent = max(date_folders, key=lambda x: x[0])
    return most_recent[1]


if __name__ == "__main__":

    previous_downloaded_audio_folder = get_most_recent_folder(STT_PATH / "stt_audio")
    upload_date = previous_downloaded_audio_folder.name
    audio_path = next(previous_downloaded_audio_folder.glob("*"))
    print(audio_path)
    video_title = audio_path.stem

    ### 1st step: Speech To Text from ORTM audio (Journal TV 20h) ###
    stt = TVNewsSpeechToText()
    stt.youtube_audio_path = audio_path

    # transcribe audio downloaded from github-actions [AnimMouse/setup-yt-dlp@v1] to text and save
    transcript_saving_path = previous_downloaded_audio_folder / f"{video_title}.txt"
    stt.transcribe_and_save(transcript_saving_path)

    ## 2nd step: Summarize the transcribed text ###
    summary = Summarizer()

    # summarize the text
    summary.auto_detect_duration_and_summarize(input_text_path=transcript_saving_path)
    summary.save_summary()

    ### 3rd step: make text to speech ###
    summarized_text_path = (
        STT_PATH / "summarized_texts" / f"{upload_date}" / f"{video_title}.txt"
    )
    tts = NewsTextToSpeech(input_text_path=summarized_text_path)
    tts.generate_and_save_audio_from_text()
