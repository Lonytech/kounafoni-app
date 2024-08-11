import time
from pathlib import Path
import os

import chainlit as cl
from langchain.schema.runnable.config import RunnableConfig

from rag import LocalRag
from models import LLMModelName

ARTICLE_SOURCE_FILE_PATH = Path(__file__).parents[1] / "data" / "malijet" / "source.csv"
# API_KEY = os.environ.get("GROQ_API_KEY")  # get API token from any secret manager if exists
API_KEY = os.getenv("GROQ_API_KEY")
SECOND_API_KEY = os.environ.get("SECOND_API_KEY")
os.environ["GROQ_API_KEY"] = SECOND_API_KEY
rag = LocalRag(data_source_path=ARTICLE_SOURCE_FILE_PATH)

os.system("curl http://localhost:11434/api/tags")
# os.system("""curl http://localhost:11434/api/pull -d '{"name": "mayflowergmbh/occiglot-7b-fr-en-instruct:latest"}'""")
# os.system("curl http://localhost:11434/api/tags")

if os.environ.get("CHATBOT_ENV") == "production" and SECOND_API_KEY:
    print("🔵 Using Groq for production mode (fast inference)...")
    rag.llm = LLMModelName.GROQ_LLAMA3

else:
    print("🔵 Using slow and free inference...")
    rag.llm = LLMModelName.OLLAMA_OCCIGLOT
    

@cl.on_chat_start
def main():

    # Build the entire RAG pipeline chain
    rag.build_rag_pipeline_chain()

    # Store the chain in the user session
    cl.user_session.set("runnable_sequence_llm_chain", rag.chain)


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
        time.sleep(.07)  # slow down Groq inference only in production

    await msg.send()
