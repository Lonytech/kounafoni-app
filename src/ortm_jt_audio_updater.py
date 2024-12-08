from pathlib import Path

from langchain_community.llms.ollama import Ollama
from langchain_groq import ChatGroq

from models import LLMModelName
from speech_to_text import TVNewsSpeechToText
from summarizer import Summarizer
from text_to_speech import NewsTextToSpeech
from utils import get_most_recent_folder

STT_PATH = Path(__file__).parents[1] / "data" / "whisper"
SUMMARIZED_TEXTS_PATH = STT_PATH / "summarized_texts"
JT_20H_PLAYLIST_URL = "https://youtube.com/playlist?list=PLDBQmURq6pOfBKc6WU0wXTg2vxAjxjQel&si=n9iNX7AUi-SpNN_N"


if __name__ == "__main__":

    # get variables
    previous_downloaded_audio_folder = get_most_recent_folder(STT_PATH / "stt_audio")
    if previous_downloaded_audio_folder:
        upload_date = previous_downloaded_audio_folder.name
        audio_path = next(previous_downloaded_audio_folder.glob("*"))
        video_title = audio_path.stem

        ### 1st step: Speech To Text from ORTM audio (Journal TV 20h) ###
        stt = TVNewsSpeechToText()
        stt.youtube_audio_path = audio_path

        # transcribe audio downloaded from github-actions [AnimMouse/setup-yt-dlp@v1] to text and save
        transcript_saving_path = (
            STT_PATH / "stt_texts" / upload_date / f"{video_title}.txt"
        )
        stt.transcribe_and_save(transcript_saving_path)

        ## 2nd step: Summarize the transcribed text ###
        summary = Summarizer(
            # llm=ChatGroq(
            #     temperature=0,
            #     model=LLMModelName.GROQ_LLAMA3.value,
            #     stop_sequences=["[END]"],
            # )
            # Default to Ollama model
        )

        # summarize the text
        summary.auto_detect_duration_and_summarize(
            input_text_path=transcript_saving_path
        )
        summary.save_summary()

        ### 3rd step: make text to speech ###
        summarized_text_path = (
            STT_PATH / "summarized_texts" / f"{upload_date}" / f"{video_title}.txt"
        )
        tts = NewsTextToSpeech(input_text_path=summarized_text_path)
        tts.generate_and_save_audio_from_text()
    else:
        print("No recent folder found.")
