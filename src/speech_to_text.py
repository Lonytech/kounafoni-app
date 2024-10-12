import textwrap
from datetime import date, datetime
from pathlib import Path

import whisper  # From OpenAI: see https://github.com/openai/whisper?tab=readme-ov-file
import yt_dlp

from utils import timeit

STT_PATH = Path(__file__).parents[1] / "data" / "whisper"
JT_20H_PLAYLIST_URL = "https://youtube.com/playlist?list=PLDBQmURq6pOfBKc6WU0wXTg2vxAjxjQel&si=n9iNX7AUi-SpNN_N"


class TVNewsSpeechToText:
    def __init__(self, youtube_link=None):
        self.youtube_link = youtube_link
        self.youtube_audio_path = None
        self.yt = None
        self.yt_info = None
        self.text_transcript_path = None
        self.transcript = None

    def get_jt_20h_by_date(self, publish_date: date):
        print("getting JT 20h...")

        # yt-dlp options to only extract metadata without downloading the video
        ydl_opts = {
            "quiet": True,  # Disable verbose logs
            "extract_flat": "in_playlist",  # Extract only metadata from the playlist, no download
        }

        # Extract metadata from the playlist
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(JT_20H_PLAYLIST_URL, download=False)

        # Loop through the videos in the playlist
        for video in reversed(playlist_info["entries"]):
            video_url = f"https://www.youtube.com/watch?v={video['id']}"
            print(video_url)

            # Get metadata for each video
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                video_info = ydl.extract_info(video_url, download=False)

            # Compare the publication date with the specified date
            video_publish_date = date(
                year=int(video_info["upload_date"][:4]),
                month=int(video_info["upload_date"][4:6]),
                day=int(video_info["upload_date"][6:]),
            )

            if video_publish_date == publish_date:
                self.youtube_link = video_url
                self.yt_info = video_info
                self.yt_info["upload_date"] = (
                    video_publish_date  # set the iso-format for date
                )
                print("Video found")
                return "JT 20h video Found"

        print("Video not found")
        return "No video matches the specified date."

    def get_last_jt_20h(self):
        # yt-dlp options to extract metadata without downloading
        ydl_opts = {
            "quiet": True,  # Disable verbose logs
            "extract_flat": "in_playlist",  # Extract only metadata, no download
        }

        # Extract metadata from the playlist
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(JT_20H_PLAYLIST_URL, download=False)

        # Get the last video URL in the playlist
        last_video = playlist_info["entries"][-1]
        last_video_url = f"https://www.youtube.com/watch?v={last_video['id']}"

        # Get metadata for each video
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            video_info = ydl.extract_info(last_video_url, download=False)

        # get video publish date in iso format
        video_publish_date = date(
            year=int(video_info["upload_date"][:4]),
            month=int(video_info["upload_date"][4:6]),
            day=int(video_info["upload_date"][6:]),
        )

        # Store the last video link for further processing
        self.youtube_link = last_video_url
        self.yt_info = last_video  # Store video info if needed
        self.yt_info["upload_date"] = video_publish_date

    @timeit
    def download_youtube_audio(self, output_path: Path):
        # Set the output path
        self.youtube_audio_path = output_path

        if not output_path.exists():
            # Create parent directories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # yt-dlp options to download the best audio and convert it to MP3
            ydl_opts = {
                "format": "bestaudio/best",  # Select the best available audio
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",  # Use FFmpeg to extract audio
                        "preferredcodec": "mp3",  # Convert audio to MP3
                        "preferredquality": "192",  # Set MP3 quality to 192 kbps
                    }
                ],
                "outtmpl": str(output_path).split(".mp3")[
                    0
                ],  # Specify the output path for the MP3 file
                "quiet": False,  # Show logs during the download
            }

            # Download and convert the audio to MP3
            print("Downloading and storing audio file...")
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.youtube_link])
                print(f"Audio file saved at {output_path}")
            except Exception as e:
                print(f"Error downloading the audio: {str(e)}")
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

    # get ORTM specific news for one date
    JT_PUBLISH_DATE = datetime.strptime("2024-09-28", "%Y-%m-%d").date()

    # get the speech to a text object
    stt = TVNewsSpeechToText()

    # JT_PUBLISH_DATE = datetime.today().date() - timedelta(days=1)
    print(JT_PUBLISH_DATE)
    stt.get_jt_20h_by_date(publish_date=JT_PUBLISH_DATE)
    stt.download_youtube_audio(
        output_path=STT_PATH
        / "stt_audio"
        / f"{stt.yt_info['upload_date']}"
        / f"{stt.yt_info['title']}.mp3"
    )
    stt.transcribe_and_save(
        write_path=STT_PATH
        / "stt_texts"
        / f"{stt.yt_info['upload_date']}"
        / f"{stt.yt_info['title']}.txt"
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
