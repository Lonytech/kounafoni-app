import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import chainlit as cl
from langchain.schema.runnable.config import RunnableConfig
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory

from models import LLMModelName, UserQuestionDateRange
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
qa_rag = LocalRag(data_source_path=ARTICLE_DIRECTORY_PATH)

# get list of models from Ollama API in logs
os.system("curl http://localhost:11434/api/tags")

if os.environ.get("CHATBOT_ENV") == "production" and SECOND_API_KEY:
    print("🔵 Using Groq for production mode (fast inference)...")
    qa_rag.llm = LLMModelName.GROQ_LLAMA3

else:
    print("🔵 Using slow and free inference...")
    qa_rag.llm = LLMModelName.OLLAMA_OCCIGLOT

### Stateful manage chat history ###
store = {}


# Manage session of chat history
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


# Make LLM infer range date of user's question if needed
def get_range_date_from_user_prompt(user_prompt: str) -> Any:

    system = (
        "Tu es un expert en extraction d'information temporelle à partir de la question de l'utilisateur. "
        "Si l'utilisateur n'indique pas d'année spécifique, prend l'année du question time."
        "Voici les instructions sur le format : {format_instructions}."
        ""
    )
    human = "{text}"
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
    parser = JsonOutputParser(pydantic_object=UserQuestionDateRange)

    if qa_rag.llm:
        chain = prompt | qa_rag.llm | parser
    else:
        raise ValueError(
            "qa_rag.llm is not available, cannot proceed with chain, initialize llm first."
        )

    result = chain.invoke(
        {
            "format_instructions": parser.get_format_instructions(),
            "text": f"{user_prompt} \nQuestion time : {datetime.now()}",
        }
    )
    return result


@cl.on_chat_start
def main() -> None:

    # Build the entire RAG pipeline chain
    qa_rag.build_rag_chain_with_memory()

    # define new session id for this chat
    qa_rag.current_session_id = str(uuid.uuid4())

    conversational_rag_chain = RunnableWithMessageHistory(
        qa_rag.memory_retrieval_chain,  # type: ignore
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    # Store the chain in the user session
    cl.user_session.set("runnable_sequence_llm_chain", conversational_rag_chain)


@cl.on_message
async def on_message(message: cl.Message) -> None:
    # Retrieve the chain from the user session
    agent = cl.user_session.get("runnable_sequence_llm_chain")

    # update basic retriever if needed for time interval purpose
    ai_infer_range_date = get_range_date_from_user_prompt(user_prompt=message.content)

    start_date, end_date = (
        ai_infer_range_date["start_date"],
        ai_infer_range_date["end_date"],
    )

    if start_date and end_date:
        start_date = int(start_date.replace("-", ""))
        end_date = int(end_date.replace("-", ""))

        time_interval_filter_in_metadata = {
            "$and": [
                {"integer_date": {"$gte": start_date}},
                {"integer_date": {"$lte": end_date}},
            ]
        }
        search_kwargs = {"filter": time_interval_filter_in_metadata, "k": 4}

        # Rebuild the entire RAG pipeline chain
        qa_rag.build_rag_chain_with_memory(retriever_search_kwargs=search_kwargs)

        # qa_rag.build_rag_chain_with_memory()
        agent = RunnableWithMessageHistory(
            qa_rag.memory_retrieval_chain,  # type: ignore
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    msg = cl.Message(content="")

    async for chunk in agent.astream(
        {"input": message.content},
        config=RunnableConfig(
            configurable={"session_id": qa_rag.current_session_id},
            callbacks=[cl.LangchainCallbackHandler()],
        ),
    ):
        if "answer" in chunk:  # check if the chunk has an answer key
            await msg.stream_token(chunk["answer"])
            time.sleep(0.03)  # slow down Groq inference only in production

    await msg.send()
