from pathlib import Path
import os

import chainlit as cl
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.prompts import PromptTemplate

from rag import LocalRag

ARTICLE_SOURCE_FILE_PATH = Path(__file__).parents[1] / "data" / "malijet" / "source.csv"
LLM_MODEL_NAME = "mayflowergmbh/occiglot-7b-fr-en-instruct"
# llm = Ollama(model="mayflowergmbh/occiglot-7b-fr-en-instruct")
template = """Question: {question}"""

if os.environ.get('CHATBOT_ENV') == 'production':
    # Pull llm and embeddings models before anything
    print("🔵 Launch Ollama...")
    os.system("ollama serve &")
    print("🔵 Retrieving models 2...")
    os.system("ollama pull mayflowergmbh/occiglot-7b-fr-en-instruct")
    os.system("ollama pull sammcj/sfr-embedding-mistral:Q4_K_M")
    print("🟢 Done in python !")

@cl.on_chat_start
def main():
    # Instantiate the chain for that user session
    prompt = PromptTemplate(template=template, input_variables=["question"])
    rag = LocalRag(data_source_path=ARTICLE_SOURCE_FILE_PATH)
    rag.llm = LLM_MODEL_NAME
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

    await msg.send()
