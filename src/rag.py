import uuid
from pathlib import Path

import pandas as pd
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter

ARTICLE_SOURCE_FILE_PATH = Path(__file__).parents[1] / "data" / "malijet" / "source.csv"
CHROMA_DB_PERSIST_PATH = Path(__file__).parents[1] / "data" / "chroma_db"
LLM_MODEL_NAME = "mayflowergmbh/occiglot-7b-fr-en-instruct"
EMBEDDING_MODEL_NAME = "sammcj/sfr-embedding-mistral:Q4_K_M"


def format_docs(docs):
    """
    Simple Doc formatter for langchain template
    :param docs:
    :return:
    """
    return "\n\n".join([d.page_content for d in docs])


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
    def llm(self, model_name):
        system_role = (
            "Tu es un expert sur les actualités du Mali et tu parles uniquement français (spécialisé en "
            "langue française)."
        )
        self._llm = Ollama(model=model_name, system=system_role)

    def load_documents(self, file_path: Path):
        print("Loading documents...")
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

    def read_vector_store(self):
        print("Loading Chroma vector store...")
        vector_store_db = Chroma(
            persist_directory=CHROMA_DB_PERSIST_PATH.as_posix(),
            embedding_function=self.embedding_model,
        )

        # Set vector store loaded
        self.vector_store_db = vector_store_db

    def update_vector_store(self):
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
        new_documents_to_embed_df.query(
            f"single_id not in {persisted_ids}", inplace=True
        )

        if new_documents_to_embed_df.empty:
            print(
                "No new document to embed. Add articles to database source to enrich the scope"
            )
        else:
            print("Embedding documents...")
            print(new_documents_to_embed_df.head())
            self.vector_store_db.add_documents(
                documents=new_documents_to_embed_df.document.tolist(),
                embedding=self.embedding_model,
                ids=new_documents_to_embed_df.single_id.tolist(),
                persist_directory=CHROMA_DB_PERSIST_PATH.as_posix(),
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
        Si tu n'as pas de réponse explicite dans le contexte, réponds "Je n'ai pas assez d'informations pour répondre 
        correctement".

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
        while True:
            input_question = input(
                "Posez moi une question sur l'actualité malienne : \n"
            )
            print(input_question)
            print(self.chain.invoke(input_question))


if __name__ == "__main__":
    rag = LocalRag(data_source_path=ARTICLE_SOURCE_FILE_PATH)
    rag.llm = LLM_MODEL_NAME
    rag.build_rag_pipeline_chain()
    rag.run_question_answer()
