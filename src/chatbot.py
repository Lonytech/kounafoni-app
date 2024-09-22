import os
import time
from pathlib import Path

import chainlit as cl
import pandas as pd
from langchain.schema.runnable.config import RunnableConfig

from models import LLMModelName
from rag import LocalRag

ARTICLE_DIRECTORY_PATH = Path(__file__).parents[1] / "data" / "articles"

if os.environ.get("CHATBOT_ENV") == "production":
    ARTICLE_DIRECTORY_PATH = (
        Path(__file__).parents[1] / "external_volume" / "data" / "articles"
    )

# Get the API KEY from ENV variables
SECOND_API_KEY = os.environ.get("SECOND_API_KEY")
SECOND_API_KEY = SECOND_API_KEY if SECOND_API_KEY else ""
os.environ["GROQ_API_KEY"] = SECOND_API_KEY

# Prepare RAG var
rag = LocalRag(data_source_path=ARTICLE_DIRECTORY_PATH)

# get list of models from Ollama API in logs
os.system("curl http://localhost:11434/api/tags")

df = pd.read_csv(
    ARTICLE_DIRECTORY_PATH / "malijet" / "2024" / "01" / "01.csv", delimiter="\t"
)
print("🔵🔵 df writing 🔵🔵")
print(df)

os.system("echo 'current dir'")
os.system("ls")
os.system("echo 'parent dir'")
os.system("ls ..")
os.system("echo 'grand parent dir'")
os.system("ls ../..")

if os.environ.get("CHATBOT_ENV") == "production" and SECOND_API_KEY:
    print("🔵 Using Groq for production mode (fast inference)...")
    rag.llm = LLMModelName.GROQ_LLAMA3

else:
    print("🔵 Using slow and free inference...")
    rag.llm = LLMModelName.OLLAMA_OCCIGLOT


@cl.on_chat_start
def main():

    # Build the entire RAG pipeline chain
    # rag.build_rag_pipeline_chain()
    # read vector store (no update needed here)
    rag.embed_documents_and_update_vector_store()
    rag.set_retriever()
    rag.build_llm_chain()

    # Store the chain in the user session
    cl.user_session.set("runnable_sequence_llm_chain", rag.chain)


# memory = ConversationSummaryBufferMemory(llm=llm, input_key='question', output_key='answer')


@cl.on_message
async def on_message(message: cl.Message):
    # Retrieve the chain from the user session
    agent = cl.user_session.get("runnable_sequence_llm_chain")  # type: Runnable

    msg = cl.Message(content="")

    async for chunk in agent.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)
        time.sleep(0.07)  # slow down Groq inference only in production

    await msg.send()
