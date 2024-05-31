import random
from functools import partial
from pathlib import Path

from langchain_community.llms import Ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from models import SummaryDuration
from speech_to_text import timeit

LLM_MODEL_NAME = "mayflowergmbh/occiglot-7b-fr-en-instruct"
SHORT_TEXT_MAXI_LENGTH = 5_000


class Summarizer:
    def __init__(self):
        self.llm = Ollama(model=LLM_MODEL_NAME, temperature=0)
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
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=5000,
                chunk_overlap=50,
                separators=[
                    "\n\n",
                    "\n",
                    ". ",
                    " ",
                    "",
                ],  # specify that sentence split (by dot) is more important than space & other
                keep_separator=False,  # drop the separators from the document after split
            )

            # get all chunks of text
            texts = text_splitter.split_text(self.text_to_summarize)

            # Summarize each part of the text
            for text in tqdm(texts):
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
        if input_text_path.exists():
            self.text_to_summarize = input_text_path.read_text()

            # TODO: Do not suppose all articles are named 'source.csv'.
            #  At this time, all of them (malijet, bamada net, etc.) have their own folder with 'source.csv' inside.
            if "source" in input_text_path.name:
                # get a random article to summarize
                self.text_to_summarize = random.choice(
                    self.text_to_summarize.split("\n")[1:-1]
                )
                print(f"Article chosen : {self.text_to_summarize[:100]}")
                print("Getting the medium summary...")
                self.get_medium_summary()

            # Youtube videos transcripts are usually long texts
            elif len(self.text_to_summarize) > SHORT_TEXT_MAXI_LENGTH:
                print(f"Article chosen : {self.text_to_summarize[:100]}")
                print("Getting the long summary...")
                self.get_long_summary()
        else:
            print("Error, input text file does not exist. Skipping...")


if __name__ == "__main__":
    summary = Summarizer()

    # From articles
    malijet_articles_path = (
        Path(__file__).parents[1] / "data" / "malijet" / "source.csv"
    )
    summary.auto_detect_duration_and_summarize(input_text_path=malijet_articles_path)
    print(summary.summarized_text)

    # From jt_20h
    jt_20h_transcript_path = (
        Path(__file__).parents[1]
        / "data"
        / "whisper"
        / "stt_texts"
        / "2024-05-24"
        / "énergie| Les enjeux de la pose de la première pierre des travaux de construction du centrale solaire.txt"
    )
    summary.auto_detect_duration_and_summarize(input_text_path=jt_20h_transcript_path)
    print(summary.summarized_text)
