import time
from pathlib import Path
import os

import chainlit as cl
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.prompts import PromptTemplate

from rag import LocalRag

ARTICLE_SOURCE_FILE_PATH = Path(__file__).parents[1] / "data" / "malijet" / "source.csv"

rag = LocalRag(data_source_path=ARTICLE_SOURCE_FILE_PATH)
if os.environ.get("CHATBOT_ENV") == "production":
    print("🔵 Using Groq for production mode (fast inference)...")
    rag.llm = "llama3-70b-8192"
else:
    print("🔵 Using slow and free inference...")
    rag.llm = "mayflowergmbh/occiglot-7b-fr-en-instruct"
    

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
