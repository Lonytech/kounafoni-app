import logging
from datetime import datetime, timedelta
from pathlib import Path

from speech_to_text import AdvancedYouTubeDownloader

# from speech_to_text import TVNewsSpeechToText
# from summarizer import Summarizer
# from text_to_speech import NewsTextToSpeech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STT_PATH = Path(__file__).parents[1] / "data" / "whisper"
SUMMARIZED_TEXTS_PATH = STT_PATH / "summarized_texts"
JT_20H_PLAYLIST_URL = "https://youtube.com/playlist?list=PLDBQmURq6pOfBKc6WU0wXTg2vxAjxjQel&si=n9iNX7AUi-SpNN_N"


if __name__ == "__main__":

    downloader = AdvancedYouTubeDownloader()
    url = "https://www.youtube.com/watch?v=wy7vxd61uwg"
    result = downloader.download_audio(url)
    if result:
        logger.info(f"Fichier téléchargé avec succès: {result}")
    else:
        logger.error("Échec du téléchargement")


# if __name__ == "__main__":
#
#     downloader = YouTubeDownloader()
#     result = downloader.download_audio("")
#     if result:
#         logger.info(f"Fichier téléchargé avec succès: {result}")
#     else:
#         logger.error("Échec du téléchargement")

# ### 1st step: Speech To Text from ORTM audio (Journal TV 20h) ###
# stt = TVNewsSpeechToText()
#
# # get ORTM news for a specific date (today)
# # JT_PUBLISH_DATE = datetime.strptime("2024-06-20", "%Y-%m-%d").date()
# JT_PUBLISH_DATE = datetime.today().date() - timedelta(days=1)  # one day before
# print(JT_PUBLISH_DATE)
#
# # Get the audio from YouTube
# stt.get_jt_20h_by_date(publish_date=JT_PUBLISH_DATE)
# stt.download_youtube_audio(
#     output_path=STT_PATH
#     / "stt_audio"
#     / f"{stt.yt_info['upload_date']}"
#     / f"{stt.yt_info['title']}.mp3"
# )
#
# # transcribe audio to text and save
# transcript_saving_path = (
#     STT_PATH / "stt_texts" / f"{stt.yt.publish_date.date()}" / f"{stt.yt.title}.txt"
# )
# stt.transcribe_and_save(transcript_saving_path)
#
# ### 2nd step: Summarize the transcribed text ###
# summary = Summarizer()
#
# # summarize the text
# summary.auto_detect_duration_and_summarize(input_text_path=transcript_saving_path)
# summary.save_summary()
#
# ### 3rd step: make text to speech ###
# summarized_text_path = (
#     STT_PATH
#     / "summarized_texts"
#     / f"{stt.yt_info['upload_date']}"
#     / f"{stt.yt_info['title']}.txt"
# )
# tts = NewsTextToSpeech(input_text_path=summarized_text_path)
# tts.generate_and_save_audio_from_text()
