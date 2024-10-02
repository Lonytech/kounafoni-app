from datetime import datetime, timedelta
from pathlib import Path

from speech_to_text import TVNewsSpeechToText
from summarizer import Summarizer
from text_to_speech import NewsTextToSpeech

STT_PATH = Path(__file__).parents[1] / "data" / "whisper"
SUMMARIZED_TEXTS_PATH = STT_PATH / "summarized_texts"
JT_20H_PLAYLIST_URL = "https://youtube.com/playlist?list=PLDBQmURq6pOfBKc6WU0wXTg2vxAjxjQel&si=n9iNX7AUi-SpNN_N"


if __name__ == "__main__":

    ### 1st step: Speech To Text from ORTM audio (Journal TV 20h) ###
    stt = TVNewsSpeechToText()

    # get ORTM news for a specific date (today)
    # JT_PUBLISH_DATE = datetime.strptime("2024-06-20", "%Y-%m-%d").date()
    JT_PUBLISH_DATE = datetime.today().date() - timedelta(days=2)  # one day before
    print(JT_PUBLISH_DATE)

    # Get the audio from YouTube
    stt.get_jt_20h_by_date(publish_date=JT_PUBLISH_DATE)
    stt.download_youtube_audio(
        output_path=STT_PATH
        / "stt_audio"
        / f"{stt.yt.publish_date.date()}"
        / f"{stt.yt.title}.wav"
    )

    # transcribe audio to text and save
    transcript_saving_path = (
        STT_PATH / "stt_texts" / f"{stt.yt.publish_date.date()}" / f"{stt.yt.title}.txt"
    )
    stt.transcribe_and_save(transcript_saving_path)

    ### 2nd step: Summarize the transcribed text ###
    summary = Summarizer()

    # summarize the text
    summary.auto_detect_duration_and_summarize(input_text_path=transcript_saving_path)
    summary.save_summary()

    ### 3rd step: make text to speech ###
    summarized_text_path = (
        STT_PATH
        / "summarized_texts"
        / f"{stt.yt.publish_date.date()}"
        / f"{stt.yt.title}.txt"
    )
    tts = NewsTextToSpeech(input_text_path=summarized_text_path)
    tts.generate_and_save_audio_from_text()
