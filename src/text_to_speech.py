import os
import random
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path

from langchain_community.llms import Ollama
from pydub import AudioSegment
from pydub.playback import play
from pydub.utils import ratio_to_db

from utils import timeit

LLM_MODEL_NAME = "mayflowergmbh/occiglot-7b-fr-en-instruct"
TMP_AUDIO_FILE_PATH = (
    Path(__file__).parents[1] / "data" / "piper" / "tts_audio" / "tmp.wav"
)
SPLIT_TEXTS_PATH = Path(__file__).parents[1] / "data" / "piper" / "split_texts"
TTS_MODELS_DIR = Path(__file__).parents[1] / "data" / "piper" / "models"
KOUNAFONI_EXPORT_APP_DIR = Path(__file__).parents[1] / "data" / "piper" / "exports"
BACKGROUND_AUDIO_PATH = (
    Path(__file__).parents[1] / "data" / "piper" / "tts_audio" / "background_jt.mp3"
)


# Get always the best quality available for now!
MAP_VOICES_AND_SPEAKERS_AVAILABLE = {
    "gilles": {
        "quality": "low",
        "nb_speakers": 1,
    },
    "siwis": {
        "quality": "medium",
        "nb_speakers": 1,
    },
    "upmc": {
        "quality": "medium",
        "nb_speakers": 2,
    },
}

MONTH_NAMES_FR = {
    1: "Janvier",
    2: "Février",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
    7: "Juillet",
    8: "Août",
    9: "Septembre",
    10: "Octobre",
    11: "Novembre",
    12: "Décembre",
}


def choose_random_voice():
    voice = random.choice(list(MAP_VOICES_AND_SPEAKERS_AVAILABLE.keys()))
    nb_speakers = MAP_VOICES_AND_SPEAKERS_AVAILABLE[voice]["nb_speakers"]
    speaker_id = random.randint(0, nb_speakers - 1) if nb_speakers > 0 else None
    return voice, speaker_id


class NewsTextToSpeech:
    def __init__(self, input_text_path: Path):
        self.input_text_path = input_text_path
        self.input_text = None
        self.publish_date = datetime.strptime(
            self.input_text_path.parent.name, "%Y-%m-%d"
        ).date()
        self.llm = Ollama(model=LLM_MODEL_NAME)
        self.voice, self.speaker_id = choose_random_voice()
        self.tts_model_name = f'fr_FR-{self.voice}-{MAP_VOICES_AND_SPEAKERS_AVAILABLE[self.voice]["quality"]}'
        self.text_to_speak_loud = None
        self.intro_toc_text = None
        self.intro_toc_text_path = None
        self.jt_20h_content_text = None
        self.jt_20h_content_text_path = None
        self.daily_voice_summary = None

    def save_split_jt_20h_texts(self, split_texts_path):
        print(f"Saving split files into {split_texts_path}  ...")
        # create the dedicated directory
        split_texts_path.mkdir(parents=True, exist_ok=True)

        # write intro
        intro_file = split_texts_path / "intro_toc_text.txt"
        intro_file.write_text(textwrap.fill(self.intro_toc_text, width=150))
        self.intro_toc_text_path = intro_file

        # write full content
        content_file = split_texts_path / "jt_20h_content_text.txt"
        content_file.write_text(textwrap.fill(self.jt_20h_content_text, width=150))
        self.jt_20h_content_text_path = content_file

    def split_jt_20h_text_to_intro_and_content(self):
        split_texts_path = SPLIT_TEXTS_PATH / self.input_text_path.name
        if split_texts_path.exists():
            print("Document have already been split and stored. Skipping...")

            self.intro_toc_text = (
                (split_texts_path / "intro_toc_text.txt").read_text().replace("\n", " ")
            )
            self.jt_20h_content_text = (
                (split_texts_path / "jt_20h_content_text.txt")
                .read_text()
                .replace("\n", " ")
            )
        else:
            # print("Using LLM to semantically divide text in two parts...") news_text: str = self.llm.invoke(
            # f""" Tu es expert en découpage de texte.
            # Découpe-moi ce texte en deux parties en utilisant ce
            # délimiteur.
            # La première partie, plus courte, est le sommaire qui se trouve au début.
            # La seconde partie
            # est le contenu qui est le reste du texte.
            # Le texte original doit rester intact !
            #
            #     Texte original :
            #     '''{self.input_text}'''
            #     """
            # )

            # news_text = " ".join(news_text.split("Première partie")[1:])

            print("Using predefined split pattern to split text in two parts...")
            news_texts = self.input_text.split("-------")

            # Introduction table of content and content retriever
            self.intro_toc_text = news_texts[0]
            self.jt_20h_content_text = news_texts[1]
            self.save_split_jt_20h_texts(split_texts_path)

    def generate_and_run_speech_command(self, speaker_reading_text):
        print(f"Generating speech from text...")
        os.system(f"""echo Hello World and {speaker_reading_text}""")
        # Generation
        generated_speech_command = f"""echo {speaker_reading_text} | piper \
        --model {self.tts_model_name} \
        --output_file {TMP_AUDIO_FILE_PATH.as_posix()} \
        --data-dir {TTS_MODELS_DIR.as_posix()} \
        --download-dir {TTS_MODELS_DIR.as_posix()} \
        --sentence-silence 1.3 \
        --length-scale 1.0 \
        {f"--speaker {self.speaker_id}" if self.speaker_id else ""} \
        """

        # Running on shell
        os.system(generated_speech_command)

    @timeit
    def build_jt_20h_intro_audio(self):
        print("Building JT 20h intro audio...")
        # get complete intro text
        introduction_sentence = f"""Bonjour, vous êtes sur Kounafôni et vous écoutez le résumé de l'actualité malienne \
        du {self.publish_date.day} {MONTH_NAMES_FR[self.publish_date.month]} {self.publish_date.year} \
        et voici le sommaire. \
        A la une, {self.intro_toc_text}"""
        introduction_sentence = introduction_sentence.replace("'", r"\'")

        # generate audio from it
        self.generate_and_run_speech_command(speaker_reading_text=introduction_sentence)

        # mix intro with background song
        intro_jt = AudioSegment.from_wav(TMP_AUDIO_FILE_PATH)
        background_sound = AudioSegment.from_mp3(BACKGROUND_AUDIO_PATH).apply_gain(
            ratio_to_db(0.25)  # volume reduced to 25%
        )
        mixed_sound = intro_jt.overlay(background_sound, loop=True)
        mixed_sound.export(TMP_AUDIO_FILE_PATH, format="wav")
        return mixed_sound

    def build_full_content_audio(self, content_text):
        print("Building full content audio...")

        # get audio from content
        self.generate_and_run_speech_command(speaker_reading_text=content_text.replace("'", r"\'"))
        # time.sleep(5)  # take time before reading from tmp_file

        return AudioSegment.from_wav(TMP_AUDIO_FILE_PATH)

    def save_audio(self, voice_summary, export_path: Path):
        print("Saving audio...")
        export_path.parent.mkdir(parents=True, exist_ok=True)
        voice_summary.export(export_path, format="mp3")
        self.daily_voice_summary = voice_summary

    def process_build_and_save_jt_20h_audio(self):
        print("Processing JT 20h audio...")
        mixed_intro = self.build_jt_20h_intro_audio()
        full_content_audio = self.build_full_content_audio(self.jt_20h_content_text)
        daily_voice_summary = mixed_intro.append(full_content_audio)
        saving_path = (
            KOUNAFONI_EXPORT_APP_DIR
            / f"{self.publish_date}"
            / f"Résumé ORTM - {self.publish_date}.mp3"
        )
        self.save_audio(voice_summary=daily_voice_summary, export_path=saving_path)

    def process_build_and_save_article_audio(self):
        print("Processing article audio...")
        full_content_audio = self.build_full_content_audio(self.input_text)
        saving_path = (
            KOUNAFONI_EXPORT_APP_DIR
            / f"{self.publish_date}"
            / f"Résumé {self.input_text_path.parent.name} - {self.publish_date} - {self.input_text[:50]}....mp3"
        )
        self.save_audio(voice_summary=full_content_audio, export_path=saving_path)

    def generate_and_save_audio_from_text(self):
        print(self.input_text_path)
        print("Starting the audio generation process...")
        if self.input_text_path.exists():
            self.input_text = (
                self.input_text_path.read_text()
                .replace("\n", " ")
                .replace(".", ". ")
                .replace("  ", " ")
            )

            # TODO: Do not suppose all articles are named 'source.csv'.
            #  At this time, all of them (malijet, bamada net, etc.) have their own folder with 'source.csv' inside.
            if "source" in self.input_text_path.name:

                # get a random article to speak loud
                self.input_text = random.choice(self.input_text.split("\n")[1:-1])
                print(f"Article chosen : {self.input_text[:100]}...")

                self.process_build_and_save_article_audio()

            # YouTube TV texts
            else:
                print(f"JT chosen : {self.input_text[:100]}...")

                self.split_jt_20h_text_to_intro_and_content()
                self.process_build_and_save_jt_20h_audio()
        else:
            sys.exit("Error, input text file does not exist. Skipping...")

    def play_generated_audio(self):
        play(self.daily_voice_summary)


if __name__ == "__main__":
    # from ORTM speech to text example
    # summarized_text = (
    #     Path(__file__).parents[1]
    #     / "data"
    #     / "whisper"
    #     / "summarized_texts"
    #     / "2024-05-24"
    #     / "🔴 Direct | JT 20H de ORTM1 du 24 mai 2024.txt"
    # )

    summarized_text = (
        Path(__file__).parents[1]
        / "data"
        / "whisper"
        / "summarized_texts"
        / "2024-05-16"
        / "Le 20heures de ORTM1 du 16 mai 2024.txt"
    )

    tts = NewsTextToSpeech(input_text_path=summarized_text)
    tts.generate_and_save_audio_from_text()
    tts.play_generated_audio()
