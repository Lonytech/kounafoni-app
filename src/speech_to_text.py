import textwrap
from datetime import date, datetime
from pathlib import Path

import moviepy.editor as mp
import whisper  # From OpenAI: see https://github.com/openai/whisper?tab=readme-ov-file
from pytube import Playlist, YouTube

from utils import timeit

STT_PATH = Path(__file__).parents[1] / "data" / "whisper"
JT_20H_PLAYLIST_URL = "https://youtube.com/playlist?list=PLDBQmURq6pOfBKc6WU0wXTg2vxAjxjQel&si=n9iNX7AUi-SpNN_N"


class TVNewsSpeechToText:
    def __init__(self, youtube_link=None):
        self.youtube_link = youtube_link
        self.youtube_audio_path = None
        self.yt = None
        self.text_transcript_path = None
        self.transcript = None

    def set_youtube_video(self):
        if self.youtube_link:
            self.yt = YouTube(url=self.youtube_link)

    def get_jt_20h_by_date(self, publish_date: date):
        print("getting JT 20h...")
        playlist = Playlist(JT_20H_PLAYLIST_URL)
        for link in reversed(playlist.video_urls):
            print(link)
            print(YouTube(link).publish_date)
            print(type(YouTube(link)))
            print(type(YouTube(link).publish_date))
            if YouTube(link).publish_date.date() == publish_date:
                self.youtube_link = link
                self.yt = YouTube(url=link)
                print("Video found")
                return "JT 20h video Found"
        print("Video not found")
        return "No video match the specified date."

    def get_last_jt_20h(self):
        playlist = Playlist(JT_20H_PLAYLIST_URL)
        last_video_url = list(playlist.video_urls)[-1]
        self.youtube_link = last_video_url
        self.yt = YouTube(last_video_url)

    @timeit
    def download_youtube_audio(self, output_path: Path):
        # set the output path
        self.youtube_audio_path = output_path

        if not output_path.exists():
            # build directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Select the best audio stream
            audio_stream = self.yt.streams.filter(only_audio=True).first()

            # Download the audio stream
            print("Downloading and storing audio file...")
            audio_stream.download(filename=f"_temp_file.mp4")

            # Convert the downloaded file to MP3
            with mp.AudioFileClip("_temp_file.mp4") as clip:
                clip.write_audiofile(output_path)

            # delete the mp4 file
            Path("_temp_file.mp4").unlink()
        else:
            print("Audio file already downloaded. Skipping...")

    @timeit
    def transcribe_and_save(self, write_path: Path):
        model_type = "small"
        model = whisper.load_model(model_type)
        print("Starting transcription...")
        print(self.youtube_audio_path)
        result = model.transcribe(
            self.youtube_audio_path.as_posix(), language="fr", verbose=False
        )
        print("Transcription Done")

        # Write the wrapped string to the file
        wrapped_text_result = textwrap.fill(result["text"], width=150)
        if not write_path.exists():
            print("Writing transcription from audio...")
            write_path.parent.mkdir(parents=True, exist_ok=True)
            write_path.write_text(wrapped_text_result)
        else:
            print("Transcription already exists. Skipping write")

        # update object
        self.transcript = result["text"]
        self.text_transcript_path = write_path


if __name__ == "__main__":
    stt = TVNewsSpeechToText()

    # get ORTM specific news for one date
    # JT_PUBLISH_DATE = datetime.strptime("2024-09-16", "%Y-%m-%d").date()
    JT_PUBLISH_DATE = datetime.today().date() - timedelta(days=1)
    print(JT_PUBLISH_DATE)
    stt.get_jt_20h_by_date(publish_date=JT_PUBLISH_DATE)
    stt.download_youtube_audio(
        output_path=STT_PATH
        / "stt_audio"
        / f"{stt.yt.publish_date.date()}"
        / f"{stt.yt.title}.wav"
    )
    stt.transcribe_and_save(
        write_path=STT_PATH
        / "stt_texts"
        / f"{stt.yt.publish_date.date()}"
        / f"{stt.yt.title}.txt"
    )

    # get last TV news
    # stt.get_last_jt_20h()
    # stt.download_youtube_audio(
    #     output_path=STT_PATH
    #     / "stt_audio"
    #     / f"{stt.yt.publish_date.date()}"
    #     / f"{stt.yt.title}.wav"
    # )
    # stt.transcribe_and_save(
    #     write_path=STT_PATH
    #     / "stt_texts"
    #     / f"{stt.yt.publish_date.date()}"
    #     / f"{stt.yt.title}.txt"
    # )
