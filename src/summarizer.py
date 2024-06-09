import random
import sys
import textwrap
from functools import partial
from pathlib import Path

from langchain_community.llms import Ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from models import SummaryDuration
from utils import timeit

SUMMARIZED_TEXTS_PATH = (
    Path(__file__).parents[1] / "data" / "whisper" / "summarized_texts"
)
LLM_MODEL_NAME = "mayflowergmbh/occiglot-7b-fr-en-instruct"
SHORT_TEXT_MAXI_LENGTH = 5_000


class Summarizer:
    def __init__(self):
        self.llm = Ollama(model=LLM_MODEL_NAME, num_thread=10)
        self.input_text_path = None
        self.text_to_summarize = None
        self.summarized_text = None

    @timeit
    def summarize(self, speech_duration: SummaryDuration):
        prompt_template = """
                Résume moi ce texte dans un format spécifique. Tu joues le rôle d'un journaliste TV et tu es chargé de 
                résumer l'actualité en {0}. Le texte résumé doit être lisible en {1}.

                "{2}"
                """

        # final summary
        summarized_text = str()

        if (
            speech_duration == SummaryDuration.SHORT_DURATION
            or speech_duration == SummaryDuration.MEDIUM_DURATION
        ):
            summarized_text = self.llm.invoke(
                prompt_template.format(
                    speech_duration.value,
                    speech_duration.value,
                    self.text_to_summarize,
                )
            )

        elif speech_duration == SummaryDuration.LONG_DURATION:
            intro_text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1_500,
                separators=[
                    "\n\n",
                    "\n",
                    ". ",
                    " ",
                    "",
                ],  # specify that sentence split (by dot) is more important than space & other
            )

            # get all chunks of text
            texts = intro_text_splitter.split_text(self.text_to_summarize)

            # Summarize each part of the text,
            # TODO:the first split is considered as "table of content" and we should
            #  make semantic context aware split to determine which part is "toc" and which part is content using an
            #  specialized llm to
            summarized_text += texts[0] + "."
            summarized_text += "\n-------\n"

            # Rejoining and split texts to longer length
            content_text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=5_000,
                separators=[
                    "\n\n",
                    "\n",
                    ". ",
                    " ",
                    "",
                ],  # specify that sentence split (by dot) is more important than space & other
            )
            texts = content_text_splitter.split_text("".join(texts[1:]))
            for text in tqdm(texts[1:]):
                summarized_text += self.llm.invoke(
                    prompt_template.format(
                        SummaryDuration.SHORT_DURATION.value,
                        SummaryDuration.SHORT_DURATION.value,
                        text,
                    )
                )
        self.summarized_text = summarized_text
        return summarized_text

    # define partial functions
    # TODO: Make short_summary imbrication within "summarize" method like other partial functions
    # def get_short_summary(self):
    #     return partial(self.summarize, speech_duration=SummaryDuration.SHORT_DURATION)

    def get_medium_summary(self):
        return partial(
            self.summarize, speech_duration=SummaryDuration.MEDIUM_DURATION
        )()

    def get_long_summary(self):
        return partial(self.summarize, speech_duration=SummaryDuration.LONG_DURATION)()

    def auto_detect_duration_and_summarize(self, input_text_path: Path):
        print(input_text_path)
        if (
            input_text_path.exists()
            and not (
                SUMMARIZED_TEXTS_PATH
                / input_text_path.parent.name
                / input_text_path.name
            ).exists()
        ):
            self.input_text_path = input_text_path
            self.text_to_summarize = input_text_path.read_text()

            # TODO: Do not suppose all articles are named 'source.csv'.
            #  At this time, all of them (malijet, bamada net, etc.) have their own folder with 'source.csv' inside.
            if "source" in input_text_path.name:
                # get a random article to summarize
                self.text_to_summarize = random.choice(
                    self.text_to_summarize.split("\n")[1:-1]
                )

                self.text_to_summarize = self.text_to_summarize.replace("\n", " ")
                print(f"Article chosen : {self.text_to_summarize[:100]}")
                print("Getting the medium summary...")
                self.get_medium_summary()

            # Youtube videos transcripts are usually long texts
            elif len(self.text_to_summarize) > SHORT_TEXT_MAXI_LENGTH:
                self.text_to_summarize = input_text_path.read_text().replace("\n", " ")
                print(f"JT chosen : {self.text_to_summarize[:100]}")
                print("Getting the long summary...")
                self.get_long_summary()
        else:
            sys.exit("Error, input text file does not exist or summarization already exists. Skipping...")

    def save_summary(self):
        summarized_text_path = (
            SUMMARIZED_TEXTS_PATH
            / self.input_text_path.parent.name
            / self.input_text_path.name
        )
        if summarized_text_path.exists():
            print("Summarization already exists, skipping...")
        else:
            print("Saving summarized text...")
            summarized_text_path.parent.mkdir(parents=True, exist_ok=True)
            wrapped_text_result = textwrap.fill(self.summarized_text, width=150)
            summarized_text_path.write_text(wrapped_text_result)


if __name__ == "__main__":
    summary = Summarizer()

    # From articles
    malijet_articles_path = (
        Path(__file__).parents[1] / "data" / "malijet" / "source.csv"
    )
    summary.auto_detect_duration_and_summarize(input_text_path=malijet_articles_path)
    print(summary.summarized_text)

    # From jt_20h
    # jt_20h_transcript_path = (
    #     Path(__file__).parents[1]
    #     / "data"
    #     / "whisper"
    #     / "stt_texts"
    #     / "2024-05-24"
    #     / "🔴 Direct | JT 20H de ORTM1 du 24 mai 2024.txt"
    # )

    # jt_20h_transcript_path = (
    #     Path(__file__).parents[1]
    #     / "data"
    #     / "whisper"
    #     / "stt_texts"
    #     / "2024-05-16"
    #     / "Le 20heures de ORTM1 du 16 mai 2024.txt"
    # )
    #
    # summary.auto_detect_duration_and_summarize(input_text_path=jt_20h_transcript_path)
    # print(summary.summarized_text)
    # summary.save_summary()
