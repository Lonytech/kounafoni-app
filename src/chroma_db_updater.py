from pathlib import Path

from langchain_community.embeddings import OllamaEmbeddings

from rag import LocalRag

ARTICLE_DIRECTORY_PATH = Path(__file__).parents[1] / "data" / "articles"
VECTOR_STORE_DIRECTORY_PATH = (
    Path(__file__).parents[1] / "data" / "vector_stores" / "chroma_db_1024"
)
EMBEDDING_MODEL_NAME = "bge-m3:567m-fp16"


def update_vectorstore() -> None:
    rag_vectorizer = LocalRag(data_source_path=ARTICLE_DIRECTORY_PATH)
    rag_vectorizer.load_documents(rag_vectorizer.data_source_path, is_directory=True)
    rag_vectorizer.split_documents()

    print("Embedding documents...")
    rag_vectorizer.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
    rag_vectorizer.embedding_model.show_progress = True

    # Load and update vector store with new
    rag_vectorizer.read_vector_store(
        vector_store_directory=VECTOR_STORE_DIRECTORY_PATH.as_posix()
    )
    rag_vectorizer.update_vector_store(
        persist_directory=VECTOR_STORE_DIRECTORY_PATH.as_posix()
    )


if __name__ == "__main__":
    update_vectorstore()
