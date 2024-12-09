import sys
import textwrap
from functools import partial
from pathlib import Path

from langchain_community.llms import Ollama
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from models import SummaryDuration
from utils import get_most_recent_folder, timeit

SUMMARIZED_TEXTS_PATH = (
    Path(__file__).parents[1] / "data" / "whisper" / "summarized_texts"
)
LLM_MODEL_NAME = "mayflowergmbh/occiglot-7b-fr-en-instruct"
SHORT_TEXT_MAXI_LENGTH = 5_000


class Summarizer:
    def __init__(
        self, llm: Ollama | ChatGroq = Ollama(model=LLM_MODEL_NAME, num_thread=10)
    ):
        self.llm = llm
        self.input_text_path: Path | None = None
        self.text_to_summarize: str = ""
        self.summarized_text: str = ""

    @timeit
    def summarize(self, speech_duration: SummaryDuration) -> None:
        prompt_template = """
            Résume moi le texte donné ci bas. Le texte résumé doit être lisible en {0}. 
            Réponds en exactement {1} mots. Ne dis rien de plus, commence ta réponse directement avec le résumé.

            Voici le texte :
            <<<{2}>>>
        """

        # final summary
        summarized_text = str()

        if (
            speech_duration == SummaryDuration.SHORT_DURATION
            or speech_duration == SummaryDuration.MEDIUM_DURATION
        ):
            new_summary = self.llm.invoke(
                prompt_template.format(
                    SummaryDuration.SHORT_DURATION.value,
                    700,  # 700 words maxi
                    self.text_to_summarize,
                )
            )

            # .content is for AI_Message in GROQ
            summarized_text = (
                str(new_summary)
                if type(new_summary) == str
                else str(new_summary.content)
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
            #  specialized llm
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

                new_summary = self.llm.invoke(
                    prompt_template.format(
                        SummaryDuration.LONG_DURATION.value,
                        int(
                            1_500 / len(texts[1:])
                        ),  # 1_500 words maxi for the whole text
                        text,
                    )
                )

                summarized_text += (
                    str(new_summary)
                    if type(new_summary) == str
                    else str(new_summary.content)
                )
        self.summarized_text = summarized_text

    # define partial functions
    # TODO: Make short_summary imbrication within "summarize" method like other partial functions
    # def get_short_summary(self):
    #     return partial(self.summarize, speech_duration=SummaryDuration.SHORT_DURATION)

    def get_medium_summary(self) -> None:
        return partial(
            self.summarize, speech_duration=SummaryDuration.MEDIUM_DURATION
        )()

    def get_long_summary(self) -> None:
        return partial(self.summarize, speech_duration=SummaryDuration.LONG_DURATION)()

    def auto_detect_duration_and_summarize(self, input_text_path: Path) -> None:
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
            # if "source" in input_text_path.name:
            #     # get a random article to summarize
            #     self.text_to_summarize = random.choice(
            #         self.text_to_summarize.split("\n")[1:-1]
            #     )
            #
            #     self.text_to_summarize = self.text_to_summarize.replace("\n", " ")
            #     print(f"Article chosen : {self.text_to_summarize[:100]}")
            #     print("Getting the medium summary...")
            #     self.get_medium_summary()

            # Youtube videos transcripts are usually long texts
            if len(self.text_to_summarize) > SHORT_TEXT_MAXI_LENGTH:
                self.text_to_summarize = input_text_path.read_text().replace("\n", " ")
                print(f"JT chosen : {self.text_to_summarize[:100]}")
                print("Getting the long summary...")
                self.get_long_summary()
            else:
                self.text_to_summarize = self.text_to_summarize.replace("\n", " ")
                print(f"Article chosen : {self.text_to_summarize[:100]}")
                print("Getting the medium summary...")
                self.get_medium_summary()
        else:
            sys.exit(
                "Error, input text file does not exist or summarization already exists. Skipping..."
            )

    def save_summary(self) -> None:
        assert (
            self.input_text_path is not None
        ), "input_text_path must be initialized as Path object"
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

    # get the main object
    summary = Summarizer()

    # From JT specific extract text
    # jt_text_path = (
    #     Path(__file__).parents[1] / "data" / "whisper" / "2024-09-30" / "🔴 Direct  JT 20H de ORTM1 du 30 Septembre 2024..txt"
    # )

    # Or latest transcribed text
    jt_text_folder = get_most_recent_folder(
        Path(__file__).parents[1] / "data" / "whisper" / "stt_texts"
    )
    print(jt_text_folder)
    if jt_text_folder:
        jt_text_path = next(jt_text_folder.glob("*"))

        summary.auto_detect_duration_and_summarize(input_text_path=jt_text_path)
        print(summary.summarized_text)
        summary.save_summary()
    else:
        print("Incorrect path submitted. Try again.")
