import os
import uuid
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.documents.base import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableSerializable
from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter

from models import LLMModelName
from utils import format_docs_to_docs, format_docs_to_string, timeit

CHROMA_DB_PERSIST_PATH = (
    Path(__file__).parents[1] / "data" / "vector_stores" / "chroma_db_1024"
)

EMBEDDING_MODEL_NAME = "bge-m3:567m-fp16"
GROQ_STOP_SEQUENCES = ["[END]"]

if os.environ.get("CHATBOT_ENV") == "production":
    print("🔵 Using cloud run volume directory to load vector store.")
    CHROMA_DB_PERSIST_PATH = (
        Path(__file__).parents[1]
        / "external_volume"
        / "data"
        / "vector_stores"
        / "chroma_db_1024"
    )


class LocalRag:
    def __init__(self, data_source_path: Path):
        self.data_source_path = data_source_path
        self.documents: list[Document] = []
        self.embedding_model: OllamaEmbeddings = OllamaEmbeddings(
            model=EMBEDDING_MODEL_NAME
        )
        self._llm: Ollama | ChatGroq = Ollama(model=LLMModelName.OLLAMA_LLAMA3.value)
        self.system_role: str = ""
        self.chain: RunnableSerializable[str, str] = RunnablePassthrough[str]()
        self.memory_retrieval_chain = None
        self.current_session_id: str = ""
        self.vector_store_db: Chroma = Chroma(
            persist_directory=CHROMA_DB_PERSIST_PATH.as_posix(),
            embedding_function=self.embedding_model,
        )
        self.retriever: VectorStoreRetriever = self.vector_store_db.as_retriever()

    @property
    def llm(self) -> Ollama | ChatGroq | None:
        return self._llm

    @llm.setter
    def llm(self, model_name: LLMModelName) -> None:
        self.system_role = """Tu es un expert sur les actualités du Mali et tu parles uniquement français 
            spécialisé en langue française. Réponds à la question uniquement grâce au contexte suivant 
            et uniquement en langue française. Il faudra clairement détailler ta réponse de manière assez verbeuse. 
            Mets en bas la source de média 'source_paper' qui t'as permis d'avoir ces réponses 
            ainsi que le lien associé (en lien hyperlink markdown 
            sous le format [Doc source_paper : Doc title](Doc link)) >> où 'source_paper', 'title' et 'link' 
            sont bien renseignés dans le contexte. S'il y a plusieurs link et plusieurs source_paper, 
            cite les deux majoritaires !
            
            Ne commence pas ta réponse par : "selon les informations ou contexte fournis" ou quelque chose de similaire, 
            réponds directement à la question.
            
            Si tu n'as pas de réponse explicite dans le contexte, 
            réponds que tu n'as pas assez d'informations pour répondre correctement à votre question 
            et uniquement dans ce cas là, ne donne pas de source."""

        if model_name == LLMModelName.OLLAMA_OCCIGLOT:
            # Launch from Ollama
            self._llm = Ollama(model=model_name.value, system=self.system_role)

        elif model_name == LLMModelName.GROQ_LLAMA3:
            # Get model from Groq LLM. Don't forget to set env variable "GROQ_API_KEY"
            self._llm = ChatGroq(
                temperature=0,
                model=model_name.value,
                stop_sequences=GROQ_STOP_SEQUENCES,
            )

    def load_documents(self, file_path: Path, is_directory: bool = True) -> None:
        print("Loading documents...")
        loader: Union[DirectoryLoader, CSVLoader]  # Explicit type for loader
        if is_directory:
            loader = DirectoryLoader(
                file_path.as_posix(),
                glob="**/*.csv",
                loader_cls=CSVLoader,
                show_progress=True,
                loader_kwargs={
                    "csv_args": {"delimiter": "\t"},
                    "metadata_columns": ["title", "source_paper", "date", "link"],
                },
            )
        else:
            loader = CSVLoader(
                file_path=file_path,
                csv_args={"delimiter": "\t"},
                metadata_columns=["title", "source_paper", "date", "link"],
            )
        self.documents = loader.load()

    def split_documents(self) -> None:
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

        # add date metadata information as integer
        for doc in self.documents:
            doc.metadata["integer_date"] = int(doc.metadata["date"].replace("-", ""))

    def read_vector_store(
        self, vector_store_directory: str = CHROMA_DB_PERSIST_PATH.as_posix()
    ) -> None:
        print("Loading Chroma vector store...")
        print("new embedding model is : ", self.embedding_model)
        print("vector_store_directory path : ", vector_store_directory)
        vector_store_db = Chroma(
            persist_directory=vector_store_directory,
            embedding_function=self.embedding_model,
        )

        # Set vector store loaded
        self.vector_store_db = vector_store_db

    def update_vector_store(
        self, persist_directory: str = CHROMA_DB_PERSIST_PATH.as_posix()
    ) -> None:
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

    def embed_documents_and_update_vector_store(self) -> None:
        print("Embedding documents...")
        self.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
        self.embedding_model.show_progress = True

        # Load and update vector store with new
        self.read_vector_store()
        self.update_vector_store()

    def set_retriever(self, search_kwargs: Optional[dict[str, Any]] = None) -> None:
        if search_kwargs is None:
            search_kwargs = {"k": 10}
        if self.vector_store_db is not None:
            print("new retriever args : ", search_kwargs)
            retriever = self.vector_store_db.as_retriever(search_kwargs=search_kwargs)
        else:
            retriever = None
        self.retriever = retriever

    def build_llm_chain(self) -> None:
        if self.llm is None:
            raise ValueError("LLM is not initialized.")

        template = (
            self.system_role
            + """
        
            Contexte : {context}
    
            Question : {question}
            """
        )

        prompt = ChatPromptTemplate.from_template(template)

        self.chain = (
            {
                "context": self.retriever | format_docs_to_string,
                "question": RunnablePassthrough[str](),
            }  # type: ignore
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def build_rag_pipeline_chain(self) -> None:
        self.load_documents(self.data_source_path)
        self.split_documents()
        self.embed_documents_and_update_vector_store()
        self.set_retriever()
        self.build_llm_chain()

    def build_rag_chain_with_memory(
        self, retriever_search_kwargs: Optional[dict[str, Any]] = None
    ) -> None:
        self.load_documents(self.data_source_path)
        self.split_documents()
        self.embed_documents_and_update_vector_store()
        self.set_retriever(search_kwargs=retriever_search_kwargs)

        ### Contextualize question ###
        contextualize_q_system_prompt = """Compte tenu de l'historique des discussions et de la dernière question 
        d'un utilisateur qui peut faire référence au contexte de l'historique des discussions, 
        formulez une question indépendante qui peut être comprise sans l'historique des discussions. 
        Ne répondez PAS à la question, reformulez-la si nécessaire ou renvoyez-la telle quelle."""

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # create chat history context
        history_aware_retriever = create_history_aware_retriever(
            llm=ChatGroq(
                temperature=0,
                model=LLMModelName.GROQ_LLAMA3.value,
                stop_sequences=GROQ_STOP_SEQUENCES,
            ),
            retriever=self.retriever | format_docs_to_docs,
            prompt=contextualize_q_prompt,
        )

        ### Answer question ###
        qa_system_prompt = """Tu es un assistant spécialisé sur les tâches de réponse aux questions. 
        Utilise les éléments de contexte suivants pour répondre à la question. 
        Réponds à la question uniquement grâce au contexte suivant et uniquement en langue française. 
        Il faudra clairement détailler ta réponse. A la fin de ta réponse, 
        mets en bas la source de média qui t'as permis d'avoir ces réponses, puis ':',
        puis le lien associé (en lien hyperlink markdown sous le format [Doc title](Doc link)) pour permettre 
        à l'utilisateur de cliquer sur le lien et aller vérifier l'information. 
        Remarque 1: S'il y a plusieurs link et plusieurs source_paper, cite les deux majoritaires !
        Remarque 3 : Ne commence pas ta réponse par : "selon les informations ou contexte fournis" 
        ou quelque chose de similaire, réponds directement à la question. Si tu n'as pas de réponse explicite 
        dans le contexte, réponds "Je n'ai pas assez d'informations pour répondre correctement à votre question."

        Contexte : {context}"""

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(
            ChatGroq(
                temperature=0,
                model=LLMModelName.GROQ_LLAMA3.value,
                stop_sequences=GROQ_STOP_SEQUENCES,
            ),
            qa_prompt,
        )
        self.memory_retrieval_chain = create_retrieval_chain(
            history_aware_retriever, question_answer_chain
        )

    @timeit
    def run_question_answer(self) -> None:
        input_question = str()
        while input_question.lower() != "bye":
            input_question = input(
                "Posez moi une question sur l'actualité malienne : \n"
            )
            print(self.chain.invoke(input_question))


if __name__ == "__main__":

    # Local test of RAG for all article published in malijet on August 2024
    ARTICLE_SOURCE_FILE_PATH = (
        Path(__file__).parents[1] / "data" / "malijet" / "2024" / "08"
    )
    rag = LocalRag(data_source_path=ARTICLE_SOURCE_FILE_PATH)
    rag.llm = LLMModelName.OLLAMA_OCCIGLOT
    rag.build_rag_pipeline_chain()
    rag.run_question_answer()
