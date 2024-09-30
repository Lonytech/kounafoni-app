import os
import time
from pathlib import Path

import chainlit as cl
from langchain.schema.runnable.config import RunnableConfig
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

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

if os.environ.get("CHATBOT_ENV") == "production" and SECOND_API_KEY:
    print("🔵 Using Groq for production mode (fast inference)...")
    rag.llm = LLMModelName.GROQ_LLAMA3

else:
    print("🔵 Using slow and free inference...")
    rag.llm = LLMModelName.OLLAMA_OCCIGLOT

### Stateful manage chat history ###
store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


@cl.on_chat_start
def main():

    # Build the entire RAG pipeline chain
    rag.build_rag_chain_with_memory()

    conversational_rag_chain = RunnableWithMessageHistory(
        rag.memory_retrieval_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    # Store the chain in the user session
    cl.user_session.set("runnable_sequence_llm_chain", conversational_rag_chain)


# memory = ConversationSummaryBufferMemory(llm=llm, input_key='question', output_key='answer')


@cl.on_message
async def on_message(message: cl.Message):
    # Retrieve the chain from the user session
    agent = cl.user_session.get("runnable_sequence_llm_chain")

    msg = cl.Message(content="")

    async for chunk in agent.astream(
        {"input": message.content},
        config=RunnableConfig(
            configurable={"session_id": "throwable_session_12345"},
            callbacks=[cl.LangchainCallbackHandler()],
        ),
    ):
        if "answer" in chunk:  # check if the chunk has an answer key
            await msg.stream_token(chunk["answer"])
            time.sleep(0.03)  # slow down Groq inference only in production

    await msg.send()
