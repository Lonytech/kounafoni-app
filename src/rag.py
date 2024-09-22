import os
import time
import uuid
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter

from models import LLMModelName
from utils import format_docs, human_readable_time

ARTICLE_SOURCE_FILE_PATH = Path(__file__).parents[1] / "data" / "malijet" / "source.csv"
CHROMA_DB_PERSIST_PATH = (
    Path(__file__).parents[1] / "data" / "vector_stores" / "chroma_db_1024"
)
# EMBEDDING_MODEL_NAME = "sammcj/sfr-embedding-mistral:Q4_K_M"
EMBEDDING_MODEL_NAME = "bge-m3:567m-fp16"

if os.environ.get("CHATBOT_ENV") == "production":
    print("🔵 Using cloud run volume directory to load vector store.")
    CHROMA_DB_PERSIST_PATH = (
        Path(__file__).parents[1]
        / "external_volume"
        / "data"
        / "vector_stores"
        / "chroma_db_1024"
    )
else:
    print("🔴 something wrong happened")


class TabSeparatorCSVLoader(CSVLoader):
    def __init__(self, file_path: str):
        super().__init__(file_path, csv_args={"delimiter": "\t"})


class LocalRag:
    def __init__(self, data_source_path: Path):
        self.data_source_path = data_source_path
        self.documents = None
        self.embedding_model = None
        self.vector_store_db = None
        self._llm = None
        self.retriever = None
        self.chain = None

    @property
    def llm(self):
        return self._llm

    @llm.setter
    def llm(self, model_name: LLMModelName):
        system_role = (
            "Tu es un expert sur les actualités du Mali et tu parles uniquement français (spécialisé en "
            "langue française)."
        )

        if model_name == LLMModelName.OLLAMA_OCCIGLOT:
            # Launch from Ollama
            self._llm = Ollama(model=model_name.value, system=system_role)

        elif model_name == LLMModelName.GROQ_LLAMA3:
            # Get model from Groq LLM. Don't forget to set env variable "GROQ_API_KEY"
            self._llm = ChatGroq(temperature=0, model=model_name.value)

    def load_documents(self, file_path: Path, is_directory=True):
        print("Loading documents...")
        if is_directory:
            loader = DirectoryLoader(
                file_path.as_posix(),
                glob="**/*.csv",
                loader_cls=CSVLoader,
                # loader_kwargs={
                #     "csv_args": {"delimiter": "\t", "autodetect_encoding": True}
                # },
            )
        else:
            loader = CSVLoader(file_path=file_path, csv_args={"delimiter": "\t"})
        self.documents = loader.load()

    def split_documents(self):
        # TODO : Define a better adaptative chunk size
        # define quantile 95% to determine automatic chunk size
        # quantile = int(
        #     pd.Series(
        #         [
        #             len(sentence)
        #             for document in self.documents
        #             for sentence in document.page_content.split(".")
        #         ]
        #     ).quantile(0.95)
        # )

        # standard value used for the first time
        quantile_default_value = 387

        # Define the maximum size of character to make sure to get all-content overlap
        maxi_character_per_words = 20

        print("Splitting documents...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=quantile_default_value,  # selected quantile
            chunk_overlap=maxi_character_per_words,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],  # specify that sentence split (by dot) is more important than space & other
            keep_separator=False,  # drop the separators from the document after split
        )

        # update documents split into chunks
        self.documents = text_splitter.split_documents(documents=self.documents)

    def create_vector_store(self):
        pass

    def read_vector_store(
        self, vector_store_directory=CHROMA_DB_PERSIST_PATH.as_posix()
    ):
        print("Loading Chroma vector store...")
        print("new embedding model is : ", self.embedding_model)
        vector_store_db = Chroma(
            persist_directory=vector_store_directory,
            embedding_function=self.embedding_model,
        )

        # Set vector store loaded
        self.vector_store_db = vector_store_db

    def update_vector_store(self, persist_directory=CHROMA_DB_PERSIST_PATH.as_posix()):
        print("Updating Chroma vector store...")
        persisted_ids = self.vector_store_db.get()["ids"]
        new_documents_to_embed_df = pd.DataFrame(
            {
                "single_id": [
                    str(uuid.uuid5(uuid.NAMESPACE_DNS, doc.page_content))
                    for doc in self.documents
                ],
                "document": self.documents,
            }
        )

        # to keep only different documents (i.e. chunks)
        new_documents_to_embed_df.drop_duplicates(subset="single_id", inplace=True)

        # Keep only documents not already embedded
        print("length persisted ids : ", len(persisted_ids))
        print(
            "length new df single ids : ",
            new_documents_to_embed_df.single_id.nunique(),
        )

        new_documents_to_embed_df.query(
            f"single_id not in {persisted_ids}", inplace=True
        )

        if new_documents_to_embed_df.empty:
            print(
                "No new document to embed. Add articles to database source to enrich the scope"
            )
        else:
            print("Embedding documents...")
            print(new_documents_to_embed_df.shape)
            print(new_documents_to_embed_df.head())
            self.vector_store_db.add_documents(
                documents=new_documents_to_embed_df.document.tolist(),
                embedding=self.embedding_model,
                ids=new_documents_to_embed_df.single_id.tolist(),
                persist_directory=persist_directory,
            )

    def delete_from_vector_store(self):
        pass

    def embed_documents_and_update_vector_store(self):
        print("Embedding documents...")
        self.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
        self.embedding_model.show_progress = True

        # Load and update vector store with new
        self.read_vector_store()
        self.update_vector_store()

    def set_retriever(self):
        if self.vector_store_db is not None:
            retriever = self.vector_store_db.as_retriever(search_kwargs={"k": 10})
        else:
            retriever = None
        self.retriever = retriever

    def build_llm_chain(self):
        template = """Réponds à la question uniquement grâce au contexte suivant et uniquement en langue française. 
        N'hésites pas à détailler ta réponse. 
        A la fin de ta réponse, mets en bas la source de média qui t'as permis d'avoir ces réponses.
        Si tu n'as pas de réponse explicite dans le contexte, réponds "Je n'ai pas assez d'informations pour répondre 
        correctement à votre question.".

        Contexte : {context}

        Question : {question}
        """

        prompt = ChatPromptTemplate.from_template(template)

        self.chain = (
            {
                "context": self.retriever | format_docs,
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def build_rag_pipeline_chain(self):
        self.load_documents(self.data_source_path)
        self.split_documents()
        self.embed_documents_and_update_vector_store()
        self.set_retriever()
        self.build_llm_chain()

    def run_question_answer(self):
        input_question = str()
        while input_question.lower() != "bye":
            start = time.perf_counter()
            input_question = input(
                "Posez moi une question sur l'actualité malienne : \n"
            )
            print(self.chain.invoke(input_question))
            end = time.perf_counter()
            elapsed_time = human_readable_time(relativedelta(seconds=int(end - start)))
            print(f" This answer took {', '.join(elapsed_time)} to execute")


if __name__ == "__main__":
    rag = LocalRag(data_source_path=ARTICLE_SOURCE_FILE_PATH)
    rag.llm = LLMModelName.GROQ_LLAMA3
    # rag.llm = LLMModelName.OLLAMA_OCCIGLOT
    rag.build_rag_pipeline_chain()
    rag.run_question_answer()
