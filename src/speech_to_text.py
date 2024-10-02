import textwrap
from datetime import date, datetime
from pathlib import Path

import moviepy.editor as mp
import whisper  # From OpenAI: see https://github.com/openai/whisper?tab=readme-ov-file
from pytubefix import Playlist, YouTube
from pytubefix.exceptions import (
    ExtractError,
    LiveStreamError,
    RegexMatchError,
    VideoUnavailable,
)

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

            # URL de la vidéo YouTube
            # video_url = "https://www.youtube.com/watch?v=XXXX"
            for client_type in [
                "WEB",
                "WEB_EMBED",
                "WEB_MUSIC",
                "WEB_CREATOR",
                "WEB_SAFARI",
                "ANDROID",
                "ANDROID_MUSIC",
                "ANDROID_CREATOR",
                "ANDROID_VR",
                "ANDROID_PRODUCER",
                "ANDROID_TESTSUITE",
                "IOS",
                "IOS_MUSIC",
                "IOS_CREATOR",
                "MWEB",
                "TV_EMBED",
                "MEDIA_CONNECT",
            ]:
                print("This is the client type --> ", client_type)
                try:
                    # Initialisation de l'objet YouTube
                    yt = YouTube(link, client_type)
                    print(f"Vidéo trouvée : {yt.title}")
                except VideoUnavailable as e:
                    print("Error for client type --> ", client_type)
                    print(e)

            try:
                # Initialisation de l'objet YouTube
                yt = YouTube(link, "WEB")
                print(f"Vidéo trouvée : {yt.title}")

                try:
                    # Tentative de récupération des streams (formats de la vidéo)
                    streams = yt.streams.filter(progressive=True, file_extension="mp4")
                    if not streams:
                        raise ValueError("Aucun flux vidéo MP4 trouvé.")

                    # Téléchargement du premier flux
                    stream = streams.first()
                    stream.download(output_path="./downloads")
                    print(f"Téléchargement réussi : {yt.title}")

                except LiveStreamError:
                    print(
                        f"Erreur : La vidéo {yt.title} est un live stream et ne peut pas être téléchargée."
                    )
                except RegexMatchError:
                    print(
                        f"Erreur : Le format de la vidéo {yt.title} ne correspond pas."
                    )
                except ExtractError:
                    print(
                        f"Erreur : Problème d'extraction des données pour la vidéo {yt.title}."
                    )
                except Exception as e:
                    print(
                        f"Erreur inattendue lors du téléchargement de {yt.title}: {str(e)}"
                    )

            except VideoUnavailable:
                print(f"Erreur : La vidéo {link} n'est pas disponible.")
            except RegexMatchError:
                print(
                    f"Erreur : L'URL de la vidéo {link} ne correspond pas au format attendu."
                )
            except Exception as e:
                print(f"Erreur inattendue lors de la lecture de {link}: {str(e)}")

            print(link)
            print(YouTube(link, "WEB"))
            print(YouTube(link, "WEB").publish_date)
            print(type(YouTube(link)))
            print(type(YouTube(link).publish_date))
            if YouTube(link) and YouTube(link).publish_date.date() == publish_date:
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
    JT_PUBLISH_DATE = datetime.strptime("2024-10-02", "%Y-%m-%d").date()
    # JT_PUBLISH_DATE = datetime.today().date() - timedelta(days=1)
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
