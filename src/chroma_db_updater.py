from rag import LocalRag
from pathlib import Path

ARTICLE_DIRECTORY_PATH = Path(__file__).parents[1] / "data" / "articles"
VECTOR_STORE_DIRECTORY_PATH = Path(__file__).parents[1] / "data" / "vector_stores" / "chroma_db_1024"
from langchain_community.embeddings import OllamaEmbeddings
EMBEDDING_MODEL_NAME = "bge-m3:567m-fp16"

# def pull_scraped_articles_from_gcs():
#     pass

def update_vectorstore():
    rag_vectorizer = LocalRag(data_source_path=ARTICLE_DIRECTORY_PATH)
    rag_vectorizer.load_documents(rag_vectorizer.data_source_path)
    rag_vectorizer.split_documents()

    print("Embedding documents...")
    rag_vectorizer.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
    rag_vectorizer.embedding_model.show_progress = True

    # Load and update vector store with new
    rag_vectorizer.read_vector_store(vector_store_directory=VECTOR_STORE_DIRECTORY_PATH.as_posix())
    rag_vectorizer.update_vector_store()


# def push_updated_vectorstore_to_gcs():
#     pass

if __name__ == "__main__":
    # pull_scraped_articles_from_gcs()
    update_vectorstore()
    # push_updated_vectorstore_to_gcs()
